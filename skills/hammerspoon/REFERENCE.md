# hammerspoon recipes

All verified live on Apple Silicon macOS. Pattern: `hs -q -c '<lua>'` — `return` the value, `hs.json.encode` for tables. Add `-t 15` to any call that touches AppleScript or many windows.

## Apps

```bash
hs -q -c 'return hs.application.frontmostApplication():name()'

# Running GUI apps (kind==1 filters out background/agent processes)
hs -q -c 'local out={} for _,a in ipairs(hs.application.runningApplications()) do
  if a:kind()==1 then out[#out+1]={name=a:name(),bundle=a:bundleID()} end end
return hs.json.encode(out)'

hs -q -c 'hs.application.launchOrFocus("Obsidian") return "ok"'
hs -q -c 'hs.application.launchOrFocusByBundleID("com.apple.Safari") return "ok"'  # deterministic; app names can differ from display names (e.g. "Microsoft Word", not "Word")

hs -q -c 'local a=hs.application.get("Music") if a then a:kill() end return "ok"'   # graceful quit; :kill9() only as last resort
hs -q -c 'local a=hs.application.get("Discord") if a then a:hide() end return "ok"'

# Window titles of one app
hs -q -c 'local t={} for _,w in ipairs(hs.application.get("Finder"):allWindows()) do t[#t+1]=w:title() end return hs.json.encode(t)'

# Click a menu item without GUI scripting (path through the menu tree)
hs -q -c 'return hs.json.encode(hs.application.get("Finder"):findMenuItem({"Window","Bring All to Front"}))'  # {"enabled":true,"ticked":false}
hs -q -c 'hs.application.get("Finder"):selectMenuItem({"Window","Bring All to Front"}) return "ok"'
```

## Browser tabs (Chrome via AppleScript; Safari: same pattern with `tell application "Safari"`, `current tab`, no `active tab index`)

```bash
# List all tabs: "window|tab|url|title" lines
hs -q -t 15 -c 'local ok,res = hs.osascript.applescript([[
tell application "Google Chrome"
  set out to {}
  set wi to 0
  repeat with w in windows
    set wi to wi + 1
    set ti to 0
    repeat with t in tabs of w
      set ti to ti + 1
      set end of out to (wi as string) & "|" & (ti as string) & "|" & (URL of t) & "|" & (title of t)
    end repeat
  end repeat
  return out
end tell]])
if not ok then return "ERROR: " .. tostring(res) end
return hs.json.encode(res)'

# Open a URL in a new tab of the front window
hs -q -t 15 -c 'local ok = hs.osascript.applescript([[
tell application "Google Chrome" to tell front window
  make new tab with properties {URL:"https://example.com/"}
end tell]]) return tostring(ok)'

# Close every tab whose URL matches (swap URL for title to match titles)
hs -q -t 15 -c 'local ok,n = hs.osascript.applescript([[
tell application "Google Chrome"
  set n to 0
  repeat with w in windows
    repeat with t in (tabs of w whose URL contains "example.com")
      close t
      set n to n + 1
    end repeat
  end repeat
  return n
end tell]]) return "closed: " .. tostring(n)'

# Focus first tab matching a pattern
hs -q -t 15 -c 'local ok,res = hs.osascript.applescript([[
tell application "Google Chrome"
  set found to ""
  repeat with w in windows
    set ti to 0
    repeat with t in tabs of w
      set ti to ti + 1
      if URL of t contains "github.com" then
        set active tab index of w to ti
        set index of w to 1
        set found to "focused"
        exit repeat
      end if
    end repeat
    if found is not "" then exit repeat
  end repeat
  return found
end tell]]) return tostring(res)'
```

## System

```bash
hs -q -c 'local d=hs.audiodevice.defaultOutputDevice() return hs.json.encode({device=d:name(),volume=d:outputVolume(),muted=d:outputMuted()})'
hs -q -c 'hs.audiodevice.defaultOutputDevice():setOutputVolume(25) return "ok"'
hs -q -c 'hs.audiodevice.defaultOutputDevice():setOutputMuted(true) return "ok"'
hs -q -c 'local t={} for _,d in ipairs(hs.audiodevice.allOutputDevices()) do t[#t+1]=d:name() end return hs.json.encode(t)'
hs -q -c 'hs.audiodevice.findOutputByName("MacBook Pro Speakers"):setDefaultOutputDevice() return "ok"'

hs -q -c 'return tostring(hs.brightness.get())'      # internal displays only — nil on desktop Macs / external monitors
hs -q -c 'hs.brightness.set(60) return "ok"'

hs -q -c 'return tostring(hs.wifi.currentNetwork())' # nil on Ethernet, wifi off, or missing Location Services permission
hs -q -c 'hs.wifi.setPower(false) return "ok"'

# Keep-awake (Caffeine): displayIdle = screen may not sleep while idle
hs -q -c 'return tostring(hs.caffeinate.get("displayIdle"))'
hs -q -c 'return "keep-awake now: " .. tostring(hs.caffeinate.toggle("displayIdle"))'

hs -q -c 'hs.caffeinate.lockScreen() return "ok"'
hs -q -c 'hs.caffeinate.systemSleep() return "ok"'

# Battery — desktop Macs return nan, and NaN makes hs.json.encode silently return nil; tostring() is safe
hs -q -c 'return tostring(hs.battery.percentage()) .. "% charging=" .. tostring(hs.battery.isCharging())'
```

## Notify & clipboard

```bash
hs -q -c 'hs.alert.show("Build done ✓", 3) return "ok"'              # transient on-screen overlay, 3s
hs -q -c 'hs.notify.new({title="Claude", informativeText="Task finished"}):send() return "ok"'  # Notification Center, persists

hs -q -c 'return hs.pasteboard.getContents()'
hs -q -c 'hs.pasteboard.setContents("text") return "ok"'

# Type text into the focused app (works where paste is blocked)
hs -q -c 'hs.eventtap.keyStrokes(hs.pasteboard.getContents()) return "ok"'
```

## Digging deeper

- Full API list: https://www.hammerspoon.org/docs/ (per module: `.../docs/hs.wifi.html`); Getting Started: https://www.hammerspoon.org/go/
- `hs -q -c 'return hs.inspect(some_table)'` pretty-prints any Lua value when JSON fails.
- Globals persist across `hs -c` calls (same Lua env) until config reload — usable as scratch state, never as durable state.
- Async state (focus changes, tab loads) doesn't settle inside one chunk — `hs.timer.usleep` blocks Hammerspoon's own main loop. Issue the action in one `hs -c`, sleep in the shell, read state in a second call.
