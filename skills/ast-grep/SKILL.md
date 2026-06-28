---
name: ast-grep
description: Write ast-grep rules for structural (AST-based) code search — matching code by structure, not text. Use when the user wants to find code patterns, locate specific language constructs, or run queries that plain text/regex search can't express ("find async functions without error handling", "calls with these args").
---

# ast-grep Code Search

Translate a natural-language query into an ast-grep rule, verify it against a sample, then run it on the codebase. Full rule syntax (atomic/relational/composite rules, metavariables, troubleshooting, worked examples) lives in [references/rule_reference.md](references/rule_reference.md) — read it when writing anything beyond a simple `pattern`.

## Prerequisite

`ast-grep --version` must work. If missing: `brew install ast-grep` (macOS), `npm i -g @ast-grep/cli`, or `cargo install ast-grep`. Invoke as `ast-grep` (the `sg` alias collides with the system `sg`).

## Workflow

1. **Clarify** — language? exact structure to match? edge cases to include/exclude?
2. **Make a sample** — write a tiny snippet that *should* match, save to a temp file.
3. **Write the rule** — start with the simplest thing that could work, then add complexity:
   - `pattern` for direct code shapes → `kind` for node types → relational (`has`/`inside`) → composite (`all`/`any`/`not`).
   - **Always add `stopBy: end` to relational rules** so they traverse the whole subtree instead of stopping at the first non-match.
4. **Test against the sample** until it matches (see Debugging below).
5. **Run on the codebase** once it matches.

## Commands

| Goal | Command |
|------|---------|
| Simple pattern search | `ast-grep run --pattern 'console.log($ARG)' --lang js .` |
| Rule-file search | `ast-grep scan --rule rule.yml /path` |
| Inline rule, no file | `ast-grep scan --inline-rules "$YAML" /path` |
| Test a rule on a snippet | `echo '<code>' \| ast-grep scan --inline-rules "$YAML" --stdin` |
| Inspect AST to find `kind` values | `ast-grep run --pattern '<code>' --lang js --debug-query=cst` |

Add `--json` to any of the above for structured output. `--debug-query` accepts `cst` (all nodes), `ast` (named nodes only), or `pattern` (how ast-grep reads your pattern).

Use `run --pattern` for simple single-node matches; use `scan` (rule file or inline) when you need relational or composite logic.

## Escaping in inline rules

The shell expands `$`, so in double-quoted `--inline-rules` write `\$VAR`, or wrap the YAML in single quotes:

```bash
ast-grep scan --inline-rules "rule: {pattern: 'console.log(\$ARG)'}" .
ast-grep scan --inline-rules 'rule: {pattern: "console.log($ARG)"}' .
```

## Debugging a rule that won't match

1. Simplify — strip sub-rules down to the smallest failing piece.
2. Confirm relational rules have `stopBy: end`.
3. `--debug-query=cst` to read the real node structure and verify your `kind` values.
4. Check metavariables are detected (see the reference's metavariable notes).

## Resources

- [references/rule_reference.md](references/rule_reference.md) — full rule syntax and worked examples.
- [ast-grep docs](https://ast-grep.github.io/) · [playground](https://ast-grep.github.io/playground.html) for testing patterns online.
