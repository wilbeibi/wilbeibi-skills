---
name: complexity-budget
description: Gate changes to existing code by comparing added complexity with expected value before and after editing. Use when adding features, fixes, flags, branches, abstractions, or parallel paths. Do NOT use for greenfield work or finished-code review (use code-review).
---

# complexity-budget

When you change existing code, the cheap move is to *add* — a new flag, a new branch, a copy-paste, a parallel path — because adding needs no understanding of the rest of the code, while folding in does. That default is how codebases rot. Before you take the additive path, make it earn its place.

**The rule:** the complexity a change adds must match what the change is worth. State the worth *first*, so you can't rationalize it after the code exists.

## Before you edit — four questions

1. **Can you build it from what's already there?** Try to get the behavior by combining existing functions, types, or config. If you can, do that — don't add a new flag, branch, or abstraction. Add a new one only when the behavior genuinely can't be composed, and then write down what it buys you.
2. **Simple, or just easy?** *Easy* = the edit closest to hand — familiar, local, no need to understand the rest of the system. *Simple* = the change that doesn't tangle two things that were separate. They're often not the same edit. Pick simple. A change that "felt small to write" can still tangle the system.
3. **Say how much it's worth — a number 0 to 1 — before you write code.** Expected usage, importance. No number, no edit. This is what stops you from spending 70% more complexity on a 10% feature.
4. **Fold in, or bolt on?** Name both options out loud: fold the new case into an existing function, vs. add a parallel path next to it. Default to folding in. Bolt on only if folding in genuinely costs more.

## After you edit — read your own diff

Read the diff yourself — you can see all of this by eye. Check in order; the first two are what matter, size alone never counts, and "a lot" is judged against a normal change *in this repo*, not in the abstract.

- **Did you couple things that were apart?** A new import across a layer; module B now reaching into module A's internals; two places that must now change together; new shared mutable state. This is the expensive kind — it makes every future change drag the other thing along.
- **Did you repeat code?** New near-duplicate blocks, copy-paste-with-edits — the program got longer without doing anything new.
- **Did one function get much hairier?** More nesting or branches in a function you touched.
- **Pasted, or moved?** A diff that's mostly *moved/refactored* lines is healthier than one that's mostly *added/pasted*.
- **Size is context only.** A big, clean, well-separated change is fine. Don't flag it for being big.

## When a check trips

Don't "approve with a warning." Do one of:

- **Fold it in** — name the existing function or type the behavior belongs in, and put it there.
- **Justify the new thing** — write the one sentence saying why it can't be composed and what it's worth.

New duplication and new cross-module coupling get defended in words or removed. Adding clean, separate code is cheap — let it through.

## Notes

- More small separate pieces beat a few tangled ones. Don't penalize adding code, files, or symbols — penalize *tangling*.
- Separate files aren't proof of separation: module B can quietly depend on module A "never returning 17." Coupling hides inside tidy folder structure.
- The worth in step 3 is your estimate, not a measurement. The point is that it exists and is visible *before* the code does.
- When a call is genuinely contested — is this worth its complexity? — see [REFERENCE.md](REFERENCE.md).
