---
name: grill-me
description: Tests whether the user understands and can defend the core decisions of their own plan, design, or shipped work, and resolves a plan's still-open decisions. Use when asked to "grill me", "quiz me", "can I defend this", to stress-test a design, to check understanding before shipping (especially AI-written code), or when karpathy-planning, state-prototype, or domain-modeling hands over open decisions. Do NOT use for one quick clarifying question, or to collect comments on a long document (use readback).
---

# grill-me

Verify that the user can explain why their system is the way it is. The output is a gap list, not a better design.

## Pick the mode

- **Defense** (default): the decisions are already made — a plan, design, PR, or shipped system. Test the user's understanding.
- **Open decisions**: another skill handed over undecided questions, or the user asks you to help decide. Go to the last section.

## Before the first round

1. Read the plan, its linked docs, and the code. Find every fact yourself, delegating to a fresh-context helper when the harness has one. Never ask the user for a fact you can look up.
2. List the core decisions: the few (3–7) that would be expensive to reverse or that shape everything else — data model, trust boundary, failure handling, the main build-vs-buy or library choice. Skip cosmetic ones.
3. For each, write yourself a private reference answer from the code: what was chosen, the real alternative, what it costs, where it breaks. Do not show it yet.

Done when every core decision has a reference answer with a `path:line` or doc cite.

## Each round

Ask at most three questions, the most consequential first. Use the user's own system, at design level — never ask for function names or line-level recall. Rotate across these classes so each core decision gets at least one:

- **Choice:** why X instead of Y? (Name a real Y.)
- **Cost:** what does X make harder or slower, and why is that acceptable?
- **Data/state:** what is stored where, who owns it, what invariant holds?
- **Failure:** what happens when Z fails, times out, or is malicious, and what does the user see then?
- **Change:** if requirement R changes, what has to move?

Shape (every slot REQUIRED; no options, no recommendation — showing either turns the test into reading comprehension):

```md
**Q1. <the decision, in a few words>**
Context: where it lives (`path:line` or doc) and what it does today, in one or two neutral sentences that do not leak the reason.
Question: <one open question from a class above>
```

After the user answers each question:

- Compare against your reference answer and the code. Say in one line each what matched, what was vague, what was wrong, then give the reference answer with its cite.
- Push once on a vague answer ("what would break if we did Y instead?"). Then move on; do not lecture.
- "The AI chose it" or "I don't know" is a gap to record, not a failure. Record it and continue.
- If the user's answer is right and the code disagrees, say so: that is a finding about the code.

Done when every core decision has been asked at least once.

## Finish

1. List each core decision under exactly one heading: **Defended** (reason and trade-off stated correctly), **Vague** (right direction, missing the cost or failure mode), **Could not explain**.
2. Mark any **Could not explain** item on a customer-facing, security, or data-loss path as blocking: the user should be able to explain it before shipping. For a PoC or throwaway experiment, list it without blocking.
3. List code/doc findings (where the user was right and the code was not) separately.
4. Offer to walk through the gaps; do not start unless asked.

## Open-decisions mode

For each undecided frontier question (prerequisites settled), at most three per round:

```md
**Q1. <the decision>**
Context: what it decides, where it shows up (`path:line`, doc, or issue), what is true today.
Options: A: <choice and its main cost>. B: <choice and its main cost>.
Recommend: B, because <one line>. "yes" accepts it.
```

Recompute the frontier after each answer. Stop when it is empty or the user accepts the remaining recommendations; summarize the decisions plus deferred branches, record hard-to-reverse ones with domain-modeling, and wait for confirmation before acting unless already authorized.

## Notes

- Reply in the user's language; keep code identifiers as they are. Explain every label (issue numbers, decision ids, acronyms) on first use.
- Defense mode follows Mitchell Hashimoto's "whiteboard defense" test for AI-assisted work. Open-decisions mode is ported from [mattpocock/skills](https://github.com/mattpocock/skills) `grilling` (MIT).
