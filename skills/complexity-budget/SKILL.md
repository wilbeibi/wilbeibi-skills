---
name: complexity-budget
description: Gate a change to existing code — decide which layer owns it, then whether the complexity it adds is worth what it buys. Use when adding a feature, fix, flag, branch, abstraction, or parallel path to code that already exists. Do NOT use for greenfield work, for one-line or mechanical edits, or for reviewing finished code (use code-review).
---

# complexity-budget

When you change existing code, the cheap move is to *add* — a new flag, a new branch, a copy-paste, a parallel path — because adding needs no understanding of the rest of the code, while folding in does. That default is how codebases rot. Before you take the additive path, make it earn its place.

**The rule:** decide *where* the change belongs before you decide *whether* it's worth it, and settle both before the code exists — afterwards you will rationalize whatever you wrote.

## Before you edit — four questions

1. **Which layer owns this?** Every question below optimizes on top of this one, so answer it first. The wrong layer is rarely the wrong idea; it's the layer that's easiest, the one that's most convenient, or **the one already open in your context**. Two tests: *where is the invariant stated?* — the fix belongs where the property it restores is established; and *if your layer vanished, would the problem remain?* — if yes it's below you, and you're patching a symptom. One countable signal: if N callers each need the same small fix, the behavior belongs beneath them.
2. **Does it add a dimension, or just a point?** First try to get the behavior by composing existing functions, types, or config — if that works, do that. If it doesn't, name a user-visible outcome that is reachable with the new thing and unreachable without it. No such outcome means it's a combination of what you already have: ship it as a preset, a recipe, or a doc, not as a new flag, branch, or abstraction.
3. **Simple, or just easy?** *Easy* = the edit closest to hand — familiar, local, no need to understand the rest of the system. *Simple* = the change that doesn't tangle two things that were separate. They're often not the same edit. Pick simple. A change that "felt small to write" can still tangle the system.
4. **Fold in, or bolt on?** Name both options out loud: fold the new case into an existing function, vs. add a parallel path next to it. Default to folding in — but only inside a trust boundary. Folding in trades duplication for coupling, and across an ownership, team, or dependency boundary that trade usually loses: copy the small thing instead. Bolt on when folding in would reach across such a boundary, or when it genuinely costs more.

Skip all four for a one-line fix, a typo, a string or config value, test data, or a pure deletion.

## After you edit — read your own diff

Read the diff yourself — you can see all of this by eye. Check in order; the first two are what matter, and "a lot" is judged against a normal change *in this repo*, not in the abstract.

- **Did you couple things that were apart?** A new import across a layer; module B now reaching into module A's internals; two places that must now change together; new shared mutable state. This is the expensive kind — it makes every future change drag the other thing along.
- **Did you repeat code — or a concept?** New near-duplicate blocks, copy-paste-with-edits: the program got longer without doing anything new. A diff that is mostly *moved/refactored* lines is healthier than one that is mostly *added/pasted*. Then ask the harder version: which existing feature is the new one most nearly parallel to? Two features that overlap 80% cost more than either alone.
- **Did the state space grow faster than the outcome space?** A new boolean doubles what your types admit. If it doesn't double what callers can actually achieve, the gap is new illegal states that you now defend by hand — in checks, in docs, and in reviewer memory.
- **Did one function get much hairier?** More nesting or branches in a function you touched.
- **A small diff at a high layer is a warning, not a comfort.** A symptom patch is almost always shorter than the fix in the layer that owns the behavior — so every check above, all of which count local damage, is biased toward the wrong-layer version. Size is otherwise context only: a big, clean, well-separated change is fine, and shouldn't be flagged for being big.

## When a check trips

Don't "approve with a warning." Do one of:

- **Fold it in** — name the existing function or type the behavior belongs in, and put it there.
- **Move it down** — name the owning layer and fix it there. If you genuinely can't (not yours, not now), keep the shim but write the displacement: which layer owns it, why the fix isn't there, and what would trigger moving it. Layer analysis is unconditional; layer compliance is negotiable but recorded.
- **Make it unrepresentable** — when two options genuinely can't be combined, don't document or validate the combination; change the shape so it can't be written. Usually a product of flags was the wrong model where a sum of variants is the right one. Where the language can't express that, fall back one step — private fields plus a single fallible constructor — and say that that is what you did.
- **Justify the new thing** — write the one sentence saying why it can't be composed and what it buys.

New duplication and new cross-module coupling get defended in words or removed. Adding clean, separate code is cheap — let it through.

## Notes

- More small separate pieces beat a few tangled ones. Don't penalize adding code, files, or symbols — penalize *tangling*.
- Separate files aren't proof of separation: module B can quietly depend on module A "never returning 17." Coupling hides inside tidy folder structure.
- Never demand another language's or project's idiom. Name the principle, then its local translation — a sum type in Go is a constructor plus unexported fields, and saying so *is* the finding.
- When a call is genuinely contested — is this worth its complexity? — see [REFERENCE.md](REFERENCE.md).
