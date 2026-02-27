---
name: m-cli
description: Swiss Army Knife for macOS - control system functions, manage utilities, and tweak preferences via the `m` CLI tool. Use ONLY when the user explicitly asks you to perform a macOS system action (e.g. "turn on dark mode", "check wifi status", "mute volume") AND the `m` command can accomplish it. Do NOT use just because macOS, wifi, display, dock, or battery topics are mentioned in a programming, informational, or troubleshooting-code context.
allowed-tools:
  - Bash
---

# m-cli: macOS System Control

Control macOS system settings, preferences, and utilities directly from the command line using the `m` command.

## When to Use

**Use this skill ONLY when all of the following are true:**
1. The user is explicitly asking Claude to **perform a system action** (not just asking about it, discussing it in code, or troubleshooting software)
2. The action targets the **local macOS system** (not a remote system, container, or VM)
3. The `m` CLI tool has a command that covers the requested action

**Good examples (use this skill):**
- "Turn on dark mode" → `m appearance dark`
- "Mute my volume" → `m volume mute`
- "Check my wifi status" → `m wifi status`
- "Hide the Dock automatically" → `m dock autohide YES`

**Bad examples (do NOT use this skill):**
- User mentions wifi/display/battery in a programming question
- User asks how to detect dark mode in their app code
- User is troubleshooting a macOS issue but wants to understand it, not run a command
- User is asking about macOS APIs or frameworks
- Any informational question about macOS topics

## Command Reference

### Appearance & Display
```bash
m appearance dark|light|auto          # Set system appearance
m display status                      # Show display info
m display brightness <0-100>          # Set brightness level
m screensaver status|on|off          # Control screensaver
```

### Network
```bash
m wifi status                         # Check WiFi status
m wifi on|off                         # Toggle WiFi
m wifi scan                           # Scan for networks
m wifi connect <SSID> [password]     # Connect to network
```

### System Controls
```bash
m lock                                # Lock screen
m sleep                               # Put system to sleep
m restart                             # Restart system
m shutdown                            # Shutdown system
```

### Dock
```bash
m dock autohide YES|NO               # Toggle dock auto-hide
m dock position bottom|left|right    # Set dock position
m dock magnification YES|NO          # Toggle magnification
m dock size <0-100>                  # Set dock size
```

### Audio & Volume
```bash
m volume <0-100>                     # Set volume level
m volume mute|unmute                 # Mute/unmute audio
m volume show                        # Show current volume
```

### Battery & Power
```bash
m battery status                     # Show battery info
m battery percentage                 # Show battery percentage
m power settings                     # Show power settings
```

### Information
```bash
m info                               # System information
m disk list                          # List disks
m disk info <disk>                   # Disk information
```

## Usage Notes
- Use `m <command> --help` to see detailed options for any command
- Some commands (like `restart`, `shutdown`) may require sudo privileges
- The `m trash` command requires Full Disk Access permission
- Always check command output for success/failure before proceeding
