// Runs once at load, after the player is defined. Build what never changes here; put what depends on the beat in
// HOOK.<sceneId> = step => {...}. A hook must give the same screen for the same step however it was reached (seeking).

// ---------- finance ----------
HOOK.fsplit = step => {
  const share = FIN.pvgo / FIN.price;
  $('fbar').innerHTML = step < 1
    ? `<div class="fillc n" style="width:100%">price ${fmt(FIN.price)}</div>`
    : `<div class="fillc g" style="width:${(1 - share) * 100}%">steady-state value ${pct(1 - share)}</div>` +
      `<div class="fillc m" style="width:${share * 100}%">PVGO ${pct(share)}</div>`;
};

$('ftab').tBodies[0].innerHTML = FIN_ROWS.map(([line, how, value], i) =>
  `<tr data-at="${i}"><td>${line}</td><td style="text-align:left">${how}</td><td class="k">${value}</td></tr>`).join('');
HOOK.ftable = step => { [...$('ftab').tBodies[0].rows].forEach((row, i) => row.classList.toggle('hl', i === step)); };

quiz('fq', 'ffb', FIN_QUIZ.roic, 0.05, {pct: true});

$('fbarsbox').innerHTML = FIN_BARS.map(b =>
  `<div class="hb"><div>capital ${fmt(b.capital)}</div>` +
  `<div class="trk"><div class="f" style="width:${b.roic / FIN_BARS[0].roic * 100}%"></div>` +
  `<i class="mark" data-at="1" style="left:${FIN.wacc / FIN_BARS[0].roic * 100}%"></i></div>` +
  `<div class="val">ROIC ${pct(b.roic)}</div></div>`).join('');
HOOK.fbars = step => {
  [...$('fbarsbox').querySelectorAll('.f')].forEach((bar, i) => bar.classList.toggle('m', step >= 2 && i === FIN_BARS.length - 1));
};

const capitalInput = $('capital-input');
capitalInput.min = CAPITAL.min;
capitalInput.max = CAPITAL.max;
capitalInput.step = CAPITAL.step;
function renderCapital(capital) {
  const result = capitalModel(capital);
  const peak = capitalModel(CAPITAL.min).roic;
  $('capital-value').textContent = fmt(result.capital);
  $('capital-roic').textContent = pct(result.roic, 1);
  $('capital-bar').style.width = result.roic / peak * 100 + '%';
  $('capital-mark').style.left = FIN.wacc / peak * 100 + '%';
  $('capital-result').textContent = `${fmt(FIN.nopat)} ÷ ${fmt(result.capital)} = ${pct(result.roic, 1)}: ${result.relation} the cost of capital.`;
}
function resetCapital() {
  capitalInput.value = CAPITAL.initial;
  renderCapital(CAPITAL.initial);
}
capitalInput.addEventListener('input', () => renderCapital(Number(capitalInput.value)));
$('capital-reset').addEventListener('click', resetCapital);
HOOK.fmodel = step => {
  capitalInput.disabled = step !== 1;
  $('capital-reset').disabled = step !== 1;
  resetCapital();
};

// ---------- RL ----------
HOOK.rleq = step => { $('rltarget').classList.toggle('hl', step >= 2); };

$('ggrid').style.gridTemplateColumns = `repeat(${GW.cols}, 1fr)`;
HOOK.rlgrid = step => {
  const last = GW.sweeps.length - 1;
  const k = [0, 0, 1, 2, last][step];
  const now = GW.sweeps[k], before = GW.sweeps[Math.max(0, k - 1)];
  $('ggrid').innerHTML = now.map((v, s) => {
    if (s === GW.wall) return '<div class="cell off"><small>wall</small></div>';
    if (s === GW.goal) return '<div class="cell g">+1<small>goal</small></div>';
    if (s === GW.pit) return '<div class="cell m">−1<small>pit</small></div>';
    const fresh = k > 0 && k < last && v !== before[s];
    const note = k === last ? GW.greedy(s)[2] : s === GW.start ? 'start' : '&nbsp;';
    return `<div class="cell${fresh ? ' hl' : ''}">${v ? v.toFixed(2) : '0'}<small>${note}</small></div>`;
  }).join('');
  $('gk').textContent = k === 0 ? 'before any sweep' : 'after sweep ' + k;
};

HOOK.rlcurve = step => {
  const shown = [10, 25, QL.steps.length][step];
  const left = 70, right = 1132, top = 40, bottom = 350, peak = Math.max(...QL.steps);
  const x = i => left + (right - left) * i / (QL.steps.length - 1);
  const y = v => bottom - (bottom - top) * v / peak;
  const ticks = [0, Math.round(peak / 2), peak];
  let svg = `<line class="ln" x1="${left}" y1="${bottom}" x2="${right}" y2="${bottom}"/><line class="ln" x1="${left}" y1="${top}" x2="${left}" y2="${bottom}"/>`;
  svg += ticks.map(t => `<text class="dim" x="${left - 12}" y="${y(t) + 6}" text-anchor="end">${t}</text>`).join('');
  svg += [1, 20, 40, 60].map(e => `<text class="dim" x="${x(e - 1)}" y="${bottom + 26}" text-anchor="middle">${e}</text>`).join('');
  svg += `<text class="dim" x="${(left + right) / 2}" y="${bottom + 50}" text-anchor="middle">episode</text><text class="dim" x="${left}" y="${top - 20}">steps to finish</text>`;
  svg += QL.steps.slice(0, shown).map((v, i) => `<circle class="dot" cx="${x(i)}" cy="${y(v)}" r="3.5"/>`).join('');
  svg += `<polyline class="msg" style="marker-end:none" points="${QL.mean.slice(0, shown).map((v, i) => x(i) + ',' + y(v)).join(' ')}"/>`;
  if (step >= 2) svg += `<line class="msg m" style="marker-end:none;stroke-dasharray:8 6" x1="${left}" y1="${y(GW.shortest)}" x2="${right}" y2="${y(GW.shortest)}"/>`;
  $('qsvg').innerHTML = svg;
};

// ---------- distributed systems ----------
HOOK.dslanes = step => {
  $('sa').textContent = step >= 3 ? 'leader · term 2' : step >= 1 ? 'candidate · term 2' : 'follower · term 1';
  $('sb').textContent = step >= 3 ? 'follower · term 2 · voted for A' : 'follower · term 1';
  $('sc').textContent = step >= 4 ? 'follower · term 2' : 'follower · term 1';
  $('na').classList.toggle('m', step >= 1 && step < 3);
  $('na').classList.toggle('g', step >= 3);
};

HOOK.dslog = step => {
  const logs = LOG_STEPS[step];
  const commit = step === 2 ? majorityIndex(LOG_STEPS[1]) : majorityIndex(logs);   // beat 2 asks; beat 3 answers
  $('lgrid').innerHTML = Object.entries(logs).map(([node, terms]) =>
    `<div class="cell" style="min-height:76px">${node}</div>` + Array.from({length: LOG_SLOTS}, (_, i) =>
      i >= terms.length ? '<div class="cell off" style="min-height:76px"></div>'
        : `<div class="cell ${i < commit ? 'g' : 'hl'}" style="min-height:76px">${i + 1}<small>term ${terms[i]}</small></div>`).join('')).join('');
  $('lci').textContent = commit;
  const holders = Object.values(logs).filter(l => l.length >= commit).length;
  $('lwhy').textContent = `entry ${commit} is on ${holders} of ${Object.keys(logs).length} nodes`;
  if (step !== 2) $('lfb').textContent = '';
};
$('lyes').onclick = () => { $('lfb').textContent = '✓ Two of three hold it: a majority.'; };
$('lno').onclick = () => { $('lfb').textContent = 'Count the nodes that hold it: A and B. That is a majority.'; };

HOOK.dsstate = step => {
  const current = ['stf', 'stc', 'stl', 'stf'][step];
  ['stf', 'stc', 'stl'].forEach(id => $(id).classList.toggle('m', id === current));
};
