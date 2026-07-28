# CLI shape

Apply systematic CLI design checks before writing or reviewing a command-line tool. Every rule is a concrete yes/no question — answer it, don't rationalize around it.

## Signature Shape

1. **Flags over positional args.** Max 2 positional args, and only when the action is primary and memorable (`cp <src> <dst>`). Everything else gets `--long-name`.
2. **Full names for every flag.** `-h` always has `--help`. `-v` always has `--verbose`. Short forms are for muscle-memory flags only.
3. **No positional args with mixed meanings.** If you have `cmd <file> <name>`, add a third thing, or the second arg means two different things across subcommands — redesign to flags.
4. **Order-independent.** `myapp --verbose subcmd` and `myapp subcmd --verbose` must both work.

## Naming

5. **Reuse flag names across subcommands.** `--json` means JSON output everywhere. `--repo` means a repository everywhere. Never use `--json` on one subcommand and `--format json` on another.
6. **Follow the standard flag table.** `-a/--all`, `-d/--debug`, `-f/--force`, `-h/--help`, `--json`, `--no-input`, `-o/--output`, `-p/--port`, `-q/--quiet`, `-u/--user`, `--version`. Deviate only with a documented reason.
7. **Verb consistency across resource subcommands.** Use the same verb set everywhere: `list`, `get`, `create`, `update`, `delete`. If one subcommand uses `remove` and another `delete`, pick one.

## Help & Discovery

8. **Progressive disclosure, three levels.** `cmd` → terse usage + one example. `cmd subcmd` → subcommand-specific params. `--help` → everything. Never dump full docs on `cmd` alone.
9. **Lead with examples, not option catalogs.** The first thing a user sees should be a working invocation they can copy.
10. **Suggest corrections on invalid input.** If the user typed a command that doesn't exist but resembles one that does, say so. "Did you mean `ps`?" not "unknown command."

## Output

11. **stdout = data, stderr = messaging.** Primary output, machine-readable output, and pipeable content go to stdout. Logs, errors, progress, and hints go to stderr.
12. **`--json` for structured output.** When a machine might consume the output, provide `--json`. Pair with a filtering flag (`--jq` or `--filter`) to let callers trim before the data leaves the tool.
13. **`--quiet` suppresses non-essential output.** Scripts should not redirect stderr to `/dev/null` — the tool should shut up when asked.
14. **Default to human-readable, provide `--plain` for grep/awk.** If terminal formatting (color, tables, dividers) would break line-based tooling, `--plain` disables it.

## Errors

15. **Every error says what happened AND what to do next.** Not "permission denied" — "permission denied: cannot write to config.yaml. Run with `--config /path/to/writable/file` or use `chmod +w config.yaml`."
16. **Never print a raw stack trace to users.** Catch expected errors and rewrite them. Unexpected errors get a debug log file path plus a bug report URL.

## Safety & Scriptability

17. **No secrets in flags.** `--password`, `--token`, `--api-key` leak to `ps` and shell history. Use `--password-file`, environment variables, or stdin.
18. **Every prompt has a flag fallback.** If the tool prompts for input interactively, provide `--name`, `--yes`, or `--confirm` so scripts don't hang.
19. **Confirm before destructive actions.** Require `--force` or interactive confirmation for anything that can't be undone. For severe destruction (deleting a server), require typing the resource name.
20. **Exit 0 on success, non-zero on failure.** Map distinct non-zero codes to distinct failure modes so scripts can branch on them.

## Function vs Form

21. **Make the default the right thing for 90% of users.** If users need a flag for the common case, the default is wrong.
22. **If an action spans multiple underlying operations, make it one command.** `merge` is one command, not `create-merge-request` + `approve` + `apply`. The user's intent is "merge this" — match it.
