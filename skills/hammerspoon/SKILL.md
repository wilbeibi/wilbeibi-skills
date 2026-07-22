---
name: hammerspoon
description: Operate macOS via Hammerspoon — run one-off `hs -c` Lua from the shell (launch/quit/focus apps, open/close/focus browser tabs, volume/wifi/caffeinate toggles, on-screen alerts, clipboard) or author persistent automations (hotkeys, watchers, menubar) in ~/.hammerspoon. Use when asked to open/close/focus an app or tab, control Mac system state, "keep my mac awake", notify on screen, or write a Hammerspoon module/hotkey — macOS only. Do NOT use for interacting with web page content (use browser tools) or cross-platform scripting.
---

# hammerspoon

One-off action = one `hs -q -c '<lua>'` call. Lasting behavior (hotkeys, watchers, menubar) = a module in `~/.hammerspoon/`. Recipes: [REFERENCE.md](REFERENCE.md).

## Readiness

`hs -q -c 'return "ok"'` must print `ok`. If not:

- exit 69 / "can't access message port" → Hammerspoon not running (`open -a Hammerspoon`) or `hs.ipc` not loaded → ensure `require("hs.ipc")` is in `~/.hammerspoon/init.lua`; the pathwatcher auto-reloads config, retry after ~2s.
- `hs` binary missing → tell the user to run `hs.ipc.cliInstall("/opt/homebrew")` in the Hammerspoon console.
- Window/app calls silently no-op → `hs -c 'return hs.accessibilityState()'` must be true; if false, user grants it in System Settings → Privacy & Security → Accessibility.

## One-off mode

```bash
hs -q -c 'hs.application.launchOrFocus("Obsidian") return "ok"'
hs -q -t 15 -c '<anything touching AppleScript or many windows>'   # default IPC timeout is 4s; busy main loop can also cause one-off "receive timeout" — retry
```

- `return` the final value or you get no output; tables print as addresses — `return hs.json.encode(tbl)` (`hs.geometry` rects need `.table`; NaN values make encode silently return nil — `tostring()` is the safe fallback).
- Single-quote the shell argument, double quotes inside Lua. Multiline: heredoc `hs -q <<'EOF' ... EOF` or `hs -q /path/file.lua` (path must start with `~`, `./`, or `/`).
- Exit codes: 65 = Lua error (message on stderr), 69 = not running / ipc missing.
- One-shot state dies: timers, watchers, and callbacks created via `hs -c` are GC'd after the call and never fire — anything that must persist or fire later is persistent mode.
- Sequencing: async state (focus change, tab load) won't settle inside one chunk, and `hs.timer.usleep` blocks Hammerspoon itself. Act in one call, `sleep` in the shell, read state in the next call.

## Persistent mode

For hotkeys/watchers/menubar items: write `~/.hammerspoon/<name>.lua`, add `require("<name>")` to `~/.hammerspoon/init.lua`. **Read `~/.hammerspoon/AGENTS.md` first** — it has the house conventions.

- Anchor timers/watchers/menubar objects in globals or module-level vars, or GC destroys them silently.
- The pathwatcher reloads config on every file save — write complete files (Write, not incremental edits), and expect `hs.reload()` to wipe all interactive globals.
- Verify after save: `hs -q -c 'return "alive"'` (reload takes ~1-2s), then check for load errors with `hs -q -c 'return hs.console.getConsole()' | tail -20`.

## Safety

- Prefer `:kill()` (graceful quit) over `:kill9()`; confirm with the user before quitting apps that may hold unsaved work.
- Never open modal dialogs (`hs.dialog`) or trigger alerts in other apps — they block event processing.
- `hs.execute` blocks Hammerspoon's main loop (freezes all its hotkeys/menubar); prefer running shell commands directly, or `hs.task` from a module.
- `hs.eventtap.keyStrokes`/clicks go to whatever is focused — only use when the user asked for exactly that.
