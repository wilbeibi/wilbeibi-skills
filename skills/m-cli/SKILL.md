---
name: m-cli
description: macOS-only system control via the `m` CLI and a shell command tool such as Bash. Use ONLY when the user explicitly asks you to perform a local macOS system action (e.g. "turn on dark mode", "check wifi status", "mute volume") AND the `m` command can accomplish it. Do NOT use just because macOS, wifi, display, dock, or battery topics are mentioned in a programming, informational, or troubleshooting-code context.
---

# m-cli: macOS System Control

Control local macOS settings with `m` only when the user explicitly asks for a system action.

## Usage

1. Confirm the request is a direct local macOS action, not a code/debugging question about macOS.
2. Check `m --help` or `m <topic> --help` when unsure.
3. Run the narrowest command and inspect output before reporting success.

## Common Commands

- Dark mode: `m appearance dark`
- Light mode: `m appearance light`
- Volume: `m volume show`, `m volume mute`, `m volume unmute`, `m volume <0-100>`
- Wi-Fi: `m wifi status`, `m wifi on`, `m wifi off`, `m wifi scan`
- Dock: `m dock autohide YES|NO`, `m dock position bottom|left|right`
- Battery/system info: `m battery status`, `m info`

## Safety Notes

- Do not run `sudo`; if a command requires it, ask the user to run it.
- Treat `restart`, `shutdown`, `sleep`, destructive file operations, and network changes as high-impact; confirm before running unless the user explicitly requested that exact action.
- `m trash` may require Full Disk Access.
- Report the command run and the observed result, not just "done".
