# write-readme — Reference

## The inverted pyramid

Journalism's inverted pyramid applied to READMEs: put the most important information first, so readers who stop early still have something complete and actionable.

```
Headline metric / one-line value prop          ← why care (most readers stop here)
─────────────────────────────────────────────
Install + quickstart                            ← remove friction first
─────────────────────────────────────────────
Why it works / evidence / benchmarks           ← earn the explanation
─────────────────────────────────────────────
Feature surface, API, CLI reference            ← for committed readers
─────────────────────────────────────────────
How it works internally / architecture         ← for contributors / skeptics
─────────────────────────────────────────────
Troubleshooting, changelog, license            ← reference tail
```

## Tool / CLI template

Use when the project is run directly (`codegraph init`, `jq`, `ripgrep`).

```markdown
<div align="center">

# ProjectName

### One-sentence tagline

**<metric 1> · <metric 2> · <metric 3>**

[badges: version · license · platform support]

</div>

## Install

<shortest possible install path — one command if possible>

<secondary paths (homebrew, scoop, cargo install) in a small table or after the primary>

## Quick start

<smallest working example — input → output, or command → result>

## Why ProjectName?

<Explain the problem in one paragraph. Then: what existing tools do, and where they fall short.>

### Benchmark / evidence

<table: metric columns (cost, tokens, time, calls) × scenario rows>

<details>
<summary>Methodology</summary>

<exact version, flags, machine, n runs, what was measured>

</details>

## Features

| Feature | Description |
|---------|-------------|
| ...     | ...         |

## Usage

<main commands with flags table>

```bash
# common invocations, one per use case
```

## Configuration

<If zero-config: say so explicitly and explain the implicit behavior (e.g., respects .gitignore).>
<If configurable: show the config file format and all keys.>

## How it works

<ASCII diagram or prose. Place AFTER quickstart — readers need to be invested first.>

## Troubleshooting

**"Error message"** — cause and fix.

**Symptom** — cause and fix.

<3–5 real issues from dogfooding or early issues.>

## License

MIT / Apache-2.0 / etc.

---

<div align="center">

**Made for <target audience>**

[Report Bug](…) · [Request Feature](…)

</div>
```

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

<Comparison table if useful: feature × library matrix. Only include competitors you've actually tested.>

## Design

<Key invariants, guarantees, and non-goals. What the library promises not to do is as important as what it does.>

## Compatibility

<Minimum language/runtime version. Breaking change policy. Semver stance.>

## Contributing

<One paragraph max. Link to CONTRIBUTING.md for details.>

## License

MIT / Apache-2.0 / etc.
```

## Badge patterns

Group badges by semantic tier — don't flatten everything into one row.

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

Use `(#)` for badges that link nowhere meaningful. Never link badges to the top of the same page.

## Progressive disclosure with `<details>`

Use `<details>` when the content matters but breaks the happy path:

- Raw benchmark data (show the summary table inline, hide the raw numbers)
- Manual / alternative setup (show the one-liner inline, hide the manual path)
- Full config reference (show the common keys inline, hide the exhaustive list)
- Contributor architecture notes

Never use `<details>` to hide content that first-time users need. If you're hiding essential information, restructure instead.

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

## Checklist

### Structure
- [ ] First visible content is a metric or differentiator, not "A library that…"
- [ ] Install / quickstart appears before the explanation
- [ ] Reader can stop after any section and have a complete, useful picture
- [ ] `<details>` used for depth, not to hide essential content

### Content
- [ ] Every capability claim has evidence or a methodology note
- [ ] At least one "where this doesn't help" sentence exists
- [ ] Troubleshooting covers 3+ real failure modes with fixes
- [ ] Zero-config behavior is called out explicitly if true
- [ ] Breaking change / compatibility policy is stated (libraries)

### Form
- [ ] Badges grouped by tier (metadata / platform / integrations)
- [ ] Feature lists are tables, not bullet prose
- [ ] Architecture diagram placed after quickstart, not before
- [ ] Footer restates the target audience
- [ ] No section exists solely to pad length — delete empty sections

### Tone
- [ ] No marketing adjectives ("powerful", "blazing", "comprehensive")
- [ ] Limits are stated alongside capabilities
- [ ] Troubleshooting is matter-of-fact, not apologetic
