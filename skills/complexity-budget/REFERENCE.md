# complexity-budget — deciding a contested call

Read this only when you're genuinely unsure whether a change is worth its complexity. The gate in [SKILL.md](SKILL.md) handles the clear cases; this is for the border.

## Why the gate exists at all

Changing existing code has two paths. Folding a new case into an existing abstraction means understanding the surrounding code; adding a branch or pasting a block beside it doesn't. So the cheap path is always additive — and an agent on defaults takes it every time, so complexity only grows. (The drift is real and measured: across large AI-assisted codebases, edits have shifted away from moving and refactoring code toward pasting and duplicating it.) The gate exists to push your own edits back toward folding in.

## Two kinds of cost — weigh tangling harder

A change adds cost two ways, and they are not equal:

1. **Repetition.** Duplication, near-clones, boilerplate. The program got longer without doing anything new. Easy to see, fixable later.
2. **Tangling.** New coupling between parts that were independent — feature A now silently affects B; module B leans on A's internals; shared mutable state. This compounds: to reason about one thing you must now hold the other in mind too. Add a tangle touching n existing parts and you've opened up to ~n new interactions. Cheap to write, increasingly expensive to understand and change.

Both are flagged in SKILL.md, but when they trade off, tangling is the one that compounds. Spend your budget removing it first.

## Simple is not easy, and not "less code"

Two traps when judging the border:

- **Easy ≠ simple.** Easy is what's near at hand — familiar, local, reachable without understanding the rest. Simple is what isn't braided together. The additive edit is usually easy *and* still complex. Judge the artifact — how the system runs, changes, and debugs months later — not how the edit felt to write. (Hickey, *Simple Made Easy*.)
- **Simple ≠ fewer things.** More small, separate pieces beat a few knotted ones. Don't credit a change for adding less code; credit it for adding less tangle. Tidy folder structure proves nothing — module B can quietly depend on module A "never returning 17."

## When to actually add a new abstraction

Question 1 of the gate says compose first. The hard case is when you can't. Add a new flag, type, or layer only when the behavior genuinely can't be expressed by composing what exists **and** the new thing pays off: it has to make many future changes shorter, by more than it costs to carry the abstraction and the interactions it opens. A new abstraction used once is a bad trade. One that absorbs a whole class of cases is a good one.

## The judgment the checks can't make for you

- Two redundant paths that reach the *same* result by different routes are cheaper than two that can *diverge*. The duplication check flags both the same; you decide which is the real risk.
- "Worth" (the 0–1 number) is your estimate, not a measurement. The gate only forces it to exist and be visible before the code does — it can't tell you it's right.
