# write-readme — Reference

## The inverted pyramid

Journalism's inverted pyramid applied to READMEs: put the most important information first, so readers who stop early still have something complete and actionable. Assume the reader is impatient and skeptical. Every line must earn its place by answering a real question, reducing risk, or changing the next action.

For agent tools, the pyramid serves both humans (top-down skimming) and AI agents (top-down scanning for command signatures and output contracts). It is not permission to paste a manpage into the README.

```
Plain outcome / strongest concrete fact        ← why care (most readers stop here)
─────────────────────────────────────────────
Install + quickstart                            ← remove friction first
─────────────────────────────────────────────
Why it exists + what it ISN'T                  ← earn the explanation, set boundaries
─────────────────────────────────────────────
Feature surface, API, CLI reference            ← only if not already covered by help/docs
─────────────────────────────────────────────
How it works internally / architecture         ← for contributors / skeptics
─────────────────────────────────────────────
Troubleshooting, changelog, license            ← reference tail
```

## Tool / CLI template

Use when the project is run directly (`codegraph init`, `jq`, `ripgrep`). For CLI tools designed to be invoked by coding agents (via bash), see the agent tool section below — the template is the same but adds agent-specific requirements.

This is a menu, not a checklist. Omit sections that repeat earlier content or belong in `--help`, generated docs, or package docs.

```markdown
<div align="center">

# ProjectName

### One-sentence tagline

</div>

<One plain sentence: what it reads/builds/changes and what output the user gets.>

<One plain sentence: when to use it.>

## Install

<shortest possible install path — one command if possible>

<secondary paths (homebrew, scoop, cargo install) in a small table or after the primary>

## Quick start

<smallest working example — input → output, or command → result>

## Why ProjectName? / Boundaries

<Explain the problem in one paragraph only if the problem is not obvious from the commands.>
<End with a clear heuristic: "Use ProjectName when X. Don't use it when Y.">

### What ProjectName is NOT

<Dedicated section with a heading. This is a trust-builder, not a disclaimer.>
<Examples: "Not a database — works on local files only." "Not for files over 100MB.">
<For agent tools, these limitations are functional guardrails that prevent agent misuse.>

### Benchmark / evidence

<table: metric columns (cost, tokens, time, calls) × scenario rows>

<details>
<summary>Methodology</summary>

<exact version, flags, machine, n runs, what was measured>

</details>

## Usage

<main commands. Prefer a compact example block over a full flags table.>

```bash
# common invocations, one per use case
```

## Screenshots / Demos

<Screenshots: crop tightly, use arrows or highlights to direct attention. The reader should understand the image without reading surrounding text or zooming.>

<Animated demos: keep under 15 seconds, 5 seconds ideal. Use WebP/AVIF for animated images or H.264 `<video>` for longer recordings. No 8MB GIFs.>

<CLI tools: show terminal recording of command → output → result. The agent sees this as expected behavior.>

## Configuration

<If zero-config: say so explicitly and explain the implicit behavior (e.g., respects .gitignore).>
<If configurable: show the config file format and all keys.>

## How it works

<ASCII diagram or prose. Place AFTER quickstart — readers need to be invested first.>

## Troubleshooting

**"Error message"** — cause and fix.

**Symptom** — cause and fix.

<Only real, common, actionable issues from dogfooding or early issues.>

## License

MIT / Apache-2.0 / etc.

<!-- Avoid footer slogans unless they add a useful link. -->
```

## Agent tool guidance

Use when the CLI tool is designed to be invoked by coding agents (via bash, not imported as a library). The README serves dual purpose: human onboarding *and* agent tool description. The agent reads the README on demand and pays the token cost only once — so the README must be scannable and unambiguous.

### Additional requirements on top of the CLI template

**Invocation must be unambiguous within 3 seconds of scanning.** The most common invocation pattern must appear within the first 30 lines.

**Arguments and important flags need to be explicit.** Agents cannot infer defaults. Show the exact command they should run, including required and recommended optional flags. Do not copy the whole `--help` output; keep the common path visible and leave exhaustive reference to the binary or generated docs.

**Show expected output format.** After every invocation example, show what success looks like and what failure looks like. Agents use this to verify their own results.

```bash
# Good: shows exact invocation + expected output
$ agent-tool --input src/ --format json
{"status": "ok", "files": 12, "warnings": []}

# Error case
$ agent-tool --input /nonexistent
{"status": "error", "message": "path not found: /nonexistent"}
```

**Keep the core interface under 200 words.** The agent's context window is precious. Put edge cases, advanced flags, and internal details behind `<details>` or link out to separate docs.

**`Not for X` warnings are functional** — they prevent the agent from using your tool for the wrong job. Be specific: "Not for files over 100MB" is better than the agent discovering it through a timeout.

**Name supported agents once.** If they affect command syntax, list the tokens where commands are shown. Avoid repeating the same support list in the hero, features, usage, and a separate support section.

## Library template

Use when the project is imported as a dependency (`import`, `require`, `use`, `go get`).

```markdown
<div align="center">

# LibName

### One-sentence tagline

**<metric or differentiator>**

[badges: version · license · language/ecosystem]

</div>

## Install

```<lang>
# package manager command
```

## Quick start

```<lang>
// minimal working example: import → configure → call → result
// show the common case, not a toy
```

## API

<For small APIs: show signatures inline with a one-line description per function.>
<For large APIs: link to generated docs and show the 20% used 80% of the time.>

| Function / Method | Description |
|-------------------|-------------|
| ...               | ...         |

## Why LibName?

<Problem → existing solutions → gap this fills. One paragraph.>
<End with a clear heuristic: "Use LibName when X. Don't use it when Y.">

<Comparison table if useful: feature × library matrix. Only include competitors you've actually tested.>

### What LibName is NOT

<Dedicated section with a heading. Key non-goals and intentional omissions.>

## Design

<Key invariants, guarantees, and non-goals. What the library promises not to do is as important as what it does.>

## Compatibility

<Minimum language/runtime version. Breaking change policy. Semver stance.>

## Contributing

<One paragraph max. Link to CONTRIBUTING.md for details.>

## License

MIT / Apache-2.0 / etc.
```

## The "Why?" section

From esbuild's README and the "Saying No" maintainer's guide: the "Why?" section is where you establish the project's mental model. It's the most important section after install.

Structure it as three beats:

1. **The problem** — one paragraph. What pain does the reader have that this solves?
2. **The gap** — what existing tools do, and where they fall short. Be specific and fair. Only mention competitors you've actually tested.
3. **The heuristic** — a clear "use this when X, don't use this when Y." This is how readers self-select and agents decide whether to invoke the tool.

Keep it tight. esbuild's entire README body is one "Why?" section and a links table. It works because it's scannable and decisive.

## "What this is NOT" / Limitations

From the "Saying No" guide: *"People choose software when its abstractions agree with their mental model."* A clear statement of what the project is NOT is as important as what it IS. It prevents scope creep, sets contributor expectations, and builds trust.

Give limitations their own heading — never bury them in a parenthetical or footnote. A named limitation reads as honest engineering; a buried caveat reads as defensive marketing.

Examples:

- **Not a database** — works on local files only. No persistence, no replication.
- **Not for files over 100MB** — performance degrades past that threshold.
- **Not a replacement for X** — if you need X, use X. This tool solves a narrower problem.
- **No network access** — operates entirely on local files. No telemetry, no API calls.

## Badge patterns

Badges are optional. Use them only when they answer an early trust question: install source, license, release version, supported platform, or CI status for a library where CI meaningfully signals compatibility. Do not keep badges as decoration.

If badges are useful, group them by semantic tier — don't flatten everything into one row.

```markdown
<!-- tier 1: package metadata -->
[![npm version](…)](…)
[![License: MIT](…)](…)

<!-- tier 2: platform / runtime support -->
[![macOS](…)](#)
[![Linux](…)](#)
[![Windows](…)](#)

<!-- tier 3: integrations / ecosystem (tool READMEs only) -->
[![Claude Code](…)](#)
[![Cursor](…)](#)
```

For agent tools, tier 3 can help only if the harness list is otherwise hard to find. If the first command block already names the supported agents, badges may be redundant.

Use `(#)` for badges that link nowhere meaningful. Never link badges to the top of the same page.

## Progressive disclosure with `<details>`

Use `<details>` when the content matters but breaks the happy path:

- Raw benchmark data (show the summary table inline, hide the raw numbers)
- Manual / alternative setup (show the one-liner inline, hide the manual path)
- Full config reference (show the common keys inline, hide the exhaustive list)
- Contributor architecture notes
- Advanced flags and edge cases (for agent tools: keep the core 80% visible, hide the long tail)

Never use `<details>` to hide content that first-time users need. If you're hiding essential information, restructure instead.

## Screenshots and demos

From Michael Lynch's release announcement guide: screenshots and terminal recordings make a README livelier and help users understand features without reading prose.

**Screenshots:**
- Crop tightly to the relevant area
- Use arrows, highlights, or annotations to direct attention
- The reader should understand the image without reading surrounding text or zooming in
- For CLI tools: prefer terminal recordings over static screenshots

**Animated demos:**
- Keep under 15 seconds, 5 seconds ideal
- Use WebP or AVIF for animated images, H.264 `<video>` for longer recordings
- Never use 8MB GIFs — they're wasteful and degrade quality
- For CLI tools: show a terminal recording of `command → output → result`. The agent sees this as expected behavior and can pattern-match its own output against it.

**Charts over raw numbers:**
- If you have benchmark data, show a graph, not a raw dump
- A single bar chart showing "old: 918ms → new: 275ms" is understood instantly; a table of 14 metrics is noise
- Raw data goes in `<details>` or a linked file

## Domain trust signals

Every tool category triggers a specific reader anxiety. Identify it and neutralize it in the opening — not the troubleshooting section.

| Category | Reader anxiety | Signal to surface early |
|----------|---------------|------------------------|
| Data analysis / monitoring | "Does this phone home?" | "100% local, no telemetry" |
| Build / CI tooling | "Will this break my pipeline?" | "Reproducible, hermetic, no side effects" |
| Auth / security libs | "Will this leak credentials?" | "No network calls", key never leaves process |
| Hot-path / perf libs | "Does this allocate? Block?" | "Zero alloc", "lock-free", benchmark result |
| Package manager / installer | "Will this trash my system?" | Isolated, reversible, explicit scope |
| Agent tool (CLI for agents) | "Will this silently corrupt my repo?" | Show diff, dry-run flag, what happens on failure |

If your tool doesn't fit a row, ask: *what would cause a cautious reader to close this tab?* Answer that question in the first two sections.

## Evidence and benchmarks

A claim without methodology is marketing. Minimum viable methodology note:

> Tested on [tool version], [n] runs per arm, median reported. [Link to raw data or script.]

Full methodology should answer:
- Exact versions of tool and dependencies
- How arms differ (with vs without, flag A vs flag B)
- Number of runs and which statistic (median, mean, p95)
- What was measured (wall time, tokens, cost — and how each was obtained)
- Hardware / environment if relevant

Show raw numbers alongside percentages. Readers who distrust percentages can verify.

**Admit the limits:** if your tool narrows gains on small inputs, or needs warm cache, or only helps on certain workloads — say so. Bounded claims are trusted; unbounded claims are ignored.

## Final pass

The steps, templates, and non-negotiables cover the structure. These are the things people miss even after reading everything else:

- The opening answers both questions *immediately*: "Is this for me?" and "How will I benefit?" If paragraph two arrives without answering both, rewrite the opening.
- Agent tools: the README will be read by a model with limited context. The most common invocation and its expected output must be findable in a 3-second scan.
- Delete duplicated facts. If supported agents, platforms, formats, or limitations appear in multiple sections, keep the version closest to the reader's action.
- Delete reference sections that only restate `--help`. Keep README reference only when it teaches relationships, defaults, or output shape that the tool itself does not make obvious.
- Read it aloud as a cautious maintainer who uses the thing. A small first-person aside can build trust when it names a real daily use. If it sounds like an ad spot, rewrite it as a plain operational fact.
