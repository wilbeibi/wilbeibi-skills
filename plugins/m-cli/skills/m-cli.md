---
name: m-cli
description: Swiss Army Knife for macOS - control system functions, manage utilities, and tweak macOS preferences from the command line. Use when user needs to manage macOS settings like dark mode, dock, wifi, battery, display, volume, or any other system preference via CLI.
allowed-tools:
  - Bash
---

# m-cli: macOS System Control

Control macOS system settings, preferences, and utilities directly from the command line using the `m` command.

## When to Use
- User asks to change system settings (dark mode, brightness, volume)
- User needs to manage system state (sleep, lock, restart)
- User wants to check system info (battery, wifi status, display settings)
- User requests dock or appearance customization
- User needs to control macOS utilities and preferences

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
