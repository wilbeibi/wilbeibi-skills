#!/usr/bin/env node
// Film a lesson page for `lesson.py video`: drive it on a virtual clock in headless Chromium and write one PNG per
// frame to stdout (for `ffmpeg -f image2pipe`). No dependencies: Chromium's DevTools protocol over node's WebSocket.
//
//   node capture.mjs '{"browser": "/usr/bin/chromium", "url": "file:///.../x.html?render=3000", "first": 1, "last": 12,
//                      "fps": 30, "scale": 1, "everyFrame": false, "trace": "/tmp/trace.json"}'
//
// The page's clock (performance.now, requestAnimationFrame, timers) is replaced before its scripts run, and every CSS
// transition and animation is paused and set to that clock, so a frame shows the page at exactly frame/fps seconds
// however long the screenshot takes. A frame is only photographed again when something on the stage changed.
// Progress goes to stderr; `trace` gets {frames, captured, seconds, late_ms, beats: [[beat, frame], ...]}.

import { spawn } from 'node:child_process';
import { once } from 'node:events';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const SHIM = `(() => {
  let now = 0, rafs = new Map(), rid = 0, timers = new Map(), tid = 0, watch = null;
  const born = new WeakMap();
  performance.now = () => now;
  window.requestAnimationFrame = cb => { rafs.set(++rid, cb); return rid; };
  window.cancelAnimationFrame = id => { rafs.delete(id); };
  window.setTimeout = (cb, ms, ...a) => { timers.set(++tid, {at: now + (+ms || 0), cb, a}); return tid; };
  window.setInterval = (cb, ms, ...a) => { timers.set(++tid, {at: now + (+ms || 0), every: Math.max(1, +ms || 0), cb, a}); return tid; };
  window.clearTimeout = window.clearInterval = id => { timers.delete(id); };
  function frame() {
    for (const [id, t] of [...timers]) if (t.at <= now && timers.has(id)) {
      if (t.every) t.at += t.every; else timers.delete(id);
      t.cb(...t.a);
    }
    const cbs = [...rafs.values()]; rafs = new Map();
    for (const cb of cbs) cb(now);
  }
  function settle() {   // pin transitions and animations to the virtual clock; returns how many are still moving
    let live = 0;
    for (const a of document.getAnimations()) {
      if (a.playState === 'finished') continue;
      if (!born.has(a)) born.set(a, now);
      const t = now - born.get(a), end = a.effect ? a.effect.getComputedTiming().endTime : 0;
      live++;
      if (t >= end) a.finish(); else { a.pause(); a.currentTime = t; }
    }
    return live;
  }
  // The film starts the lesson itself, so the first beat's animations are created and pinned inside one task, like every
  // later beat's. Left to start at page load they sometimes reach the compositor first and their text is drawn differently.
  window.__start = beat => {
    watch = new MutationObserver(() => {});
    watch.observe(document.getElementById('stage'), {subtree: true, childList: true, attributes: true, characterData: true});
    go(beat); play(); frame(); settle();
  };
  window.__seek = t => {
    let live = 0;
    while (now < t - 1e-6) { now = Math.min(t, now + 1000 / 60); frame(); live += settle(); }
    return JSON.stringify({idx, dirty: live > 0 || watch.takeRecords().length > 0, errors: window.__ERR});
  };
})();`;

const spec = JSON.parse(process.argv[2]);
const fail = msg => { console.error('capture: ' + msg); process.exit(1); };
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'lesson-film-'));
const chrome = spawn(spec.browser, ['--headless=new', '--disable-gpu', '--hide-scrollbars', '--mute-audio', '--no-first-run',
  '--allow-file-access-from-files', `--user-data-dir=${profile}`, '--window-size=1280,720', '--force-device-scale-factor=1',
  '--remote-debugging-port=0', 'about:blank'], {stdio: ['ignore', 'ignore', 'pipe']});
const cleanup = () => { try { chrome.kill('SIGKILL'); } catch {} try { fs.rmSync(profile, {recursive: true, force: true}); } catch {} };
process.on('exit', cleanup);
for (const sig of ['SIGINT', 'SIGTERM', 'SIGPIPE']) process.on(sig, () => process.exit(130));
process.stdout.on('error', () => process.exit(1));   // ffmpeg went away

const port = await new Promise((resolve, reject) => {
  let err = '';
  chrome.stderr.on('data', d => { err += d; const m = err.match(/DevTools listening on ws:\/\/[^:]+:(\d+)\//); if (m) resolve(m[1]); });
  chrome.on('exit', code => reject(new Error(`browser exited (${code}) before DevTools came up: ${err.slice(-300)}`)));
  setTimeout(() => reject(new Error('browser did not open DevTools within 30 s')), 30000).unref();
}).catch(e => fail(e.message));
const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
const ws = new WebSocket(targets.find(t => t.type === 'page').webSocketDebuggerUrl);
await once(ws, 'open');
let seq = 0;
const pending = new Map(), waiting = new Map();
ws.addEventListener('message', e => {
  const msg = JSON.parse(e.data);
  if (msg.id) { const p = pending.get(msg.id); pending.delete(msg.id); msg.error ? p.reject(new Error(msg.error.message)) : p.resolve(msg.result); }
  else if (waiting.has(msg.method)) { waiting.get(msg.method)(msg.params); waiting.delete(msg.method); }
});
const send = (method, params = {}) => new Promise((resolve, reject) => { pending.set(++seq, {resolve, reject}); ws.send(JSON.stringify({id: seq, method, params})); });
const event = method => new Promise(resolve => waiting.set(method, resolve));
const evaluate = async expression => {
  const r = await send('Runtime.evaluate', {expression, returnByValue: true});
  if (r.exceptionDetails) fail(`${expression.slice(0, 40)}: ${r.exceptionDetails.exception?.description || r.exceptionDetails.text}`);
  return r.result.value;
};

await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', {width: 1280, height: 720, deviceScaleFactor: spec.scale || 1, mobile: false});
await send('Page.addScriptToEvaluateOnNewDocument', {source: SHIM});
const loaded = event('Page.loadEventFired');
await send('Page.navigate', {url: spec.url});
await loaded;

const page = JSON.parse(await evaluate(`JSON.stringify(typeof CUM === 'undefined' ? {errors: window.__ERR || ['the page script did not run']} :
  {cum: CUM, total: TOTAL, speed, errors: window.__ERR, unclocked: [...new Set([...document.querySelectorAll('canvas,video,animate,animateTransform,animateMotion,set')].map(e => e.tagName.toLowerCase()))]})`));
if (page.errors.length) fail('page error: ' + page.errors.join('; '));
const first = (spec.first || 1) - 1, last = Math.min(spec.last ?? page.cum.length, page.cum.length);   // beats first+1 .. last, 1-based
if (!(first >= 0 && first < last)) fail(`beats ${spec.first}-${spec.last} are not in this lesson of ${page.cum.length}`);
const end = last < page.cum.length ? page.cum[last] : page.total;
const seconds = (end - page.cum[first]) / page.speed / 1000;
const frames = Math.ceil(seconds * spec.fps - 1e-6);
let everyFrame = !!spec.everyFrame;
if (page.unclocked.length && !everyFrame) {
  everyFrame = true;
  console.error(`capture: the page has <${page.unclocked.join('>, <')}>: photographing every frame. A canvas follows the clock only if it draws from requestAnimationFrame; SMIL and <video> do not follow it at all`);
}

await evaluate(`__start(${first})`);
const beats = [[first + 1, 0]];
let shot = null, captured = 0, seen = first;
const began = Date.now();
for (let f = 0; f < frames; f++) {
  const state = JSON.parse(await evaluate(`__seek(${f * 1000 / spec.fps})`));
  if (state.errors.length) fail(`page error at frame ${f}: ` + state.errors.join('; '));
  if (state.idx !== seen) { seen = state.idx; beats.push([seen + 1, f]); }
  if (!shot || state.dirty || everyFrame) {
    shot = Buffer.from((await send('Page.captureScreenshot', {format: 'png', optimizeForSpeed: true})).data, 'base64');
    captured++;
  }
  if (!process.stdout.write(shot)) await once(process.stdout, 'drain');
  if (f % (spec.fps * 10) === 0 || f === frames - 1)
    console.error(`film ${String(f + 1).padStart(6)}/${frames}  beat ${seen + 1}  ${captured} photographed  ${Math.round((Date.now() - began) / 1000)} s`);
}
// how long after its time each beat appeared: 0 .. one frame is the best a frame grid can do
const late = beats.map(([beat, f]) => f * 1000 / spec.fps - (page.cum[beat - 1] - page.cum[first]) / page.speed);
if (spec.trace) fs.writeFileSync(spec.trace, JSON.stringify({frames, captured, seconds, first: first + 1, last: seen + 1, expected_last: last,
  late_ms: [Math.min(...late), Math.max(...late)], beats}));
await new Promise(resolve => process.stdout.end(resolve));
ws.close();
process.exit(0);
