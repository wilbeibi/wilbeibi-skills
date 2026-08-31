# complexity-budget — deciding a contested call

Read this only when you're genuinely unsure whether a change is worth its complexity. The gate in [SKILL.md](SKILL.md) handles the clear cases; this is for the border.

## Why the gate exists at all

Changing existing code has two paths. Folding a new case into an existing abstraction means understanding the surrounding code; adding a branch or pasting a block beside it doesn't. So the cheap path is always additive — and an agent on defaults takes it every time, so complexity only grows. (GitClear's analyses of large AI-assisted codebases report a shift away from moved and refactored lines toward pasted and duplicated ones. Its line-level method can't separate real duplication from legitimate boilerplate, so read it as a direction, not a measurement.) The gate exists to push your own edits back toward folding in.

## Why the layer question comes first

Complexity is not a property of a change; it's a property of (change, layer). The same behavior implemented at the wrong layer can cost an order of magnitude more — and the wrong-layer version is almost always the one with the *smaller diff*, because a symptom patch is five lines where the fix in the owning layer is fifty plus a migration. Every heuristic that scores local damage, including all of SKILL.md's after-edit checks, is therefore structurally biased toward the wrong layer. That is why layer is question 1, and why the small-diff warning exists to counterweight the rest of the list.

Wrong layer is also the *cause* of tangling, not merely a sibling of it: when layer N fixes a problem owned by layer N−2, layer N has to encode an assumption about N−2's behavior. That is how "module B depends on A never returning 17" gets written in the first place.

The third attractor named in question 1 — *the layer you already own* — is structural rather than cognitive: fixes land on org boundaries instead of problem boundaries, which is Conway's law applied to bug fixing. Its observable symptom is the same bug fixed N times in N teams' layers, none of them the owning one, so "has this been fixed somewhere else before?" is the cheapest wrong-layer detector available. For an agent the same attractor is the file already in its context.

## Two kinds of cost — weigh tangling harder

A change adds cost two ways, and they are not equal:

1. **Repetition.** Duplication, near-clones, boilerplate. The program got longer without doing anything new. Easy to see, fixable later.
2. **Tangling.** New coupling between parts that were independent — feature A now silently affects B; module B leans on A's internals; shared mutable state. This compounds: to reason about one thing you must now hold the other in mind too. Add a tangle touching n existing parts and you've opened up to ~n new interactions. Cheap to write, increasingly expensive to understand and change.

Both are flagged in SKILL.md, but when they trade off, tangling is the one that compounds. Spend your budget removing it first.

## Simple is not easy, and not "less code"

Two traps when judging the border:

- **Easy ≠ simple.** Easy is what's near at hand — familiar, local, reachable without understanding the rest. Simple is what isn't braided together. The additive edit is usually easy *and* still complex. Judge the artifact — how the system runs, changes, and debugs months later — not how the edit felt to write. (Hickey, *Simple Made Easy*.)
- **Simple ≠ fewer things.** More small, separate pieces beat a few knotted ones. Don't credit a change for adding less code; credit it for adding less tangle. Tidy folder structure proves nothing — module B can quietly depend on module A "never returning 17."

## Orthogonality — what the gate says yes to

Tangling is a negative frame: it can only say no. The positive version is Pike's — good features "cover the space, like a vector basis covering solution space," orthogonal and interacting predictably. That is what question 2 is really asking. A feature that is a linear combination of existing ones adds zero dimensions; it's a point that was already reachable. Non-orthogonal features charge you twice: users must learn the difference between two nearly-parallel things, and every later feature has to be reasoned about against both — n entangled features leave O(n²) interactions to keep straight where orthogonal ones leave O(n).

Three limits, because the metaphor is not the thing:

- Vector spaces are linear and their dimensions cost the same; real features don't. Orthogonality tells you whether a feature is worth having, not whether you can afford to build it.
- Composition isn't free. A and B together can produce behavior neither has — sometimes that's the whole payoff, sometimes it's an illegal state.
- Maximally orthogonal primitives produce a toolkit the user has to assemble. Products need a convenience layer, which is where this rejoins the layer question: keep the core orthogonal, and let non-orthogonal conveniences live in a layer above it, expressed in the core's terms.

## When a combination is genuinely illegal

The constraint exists whether or not you encode it; you only choose where it lives. Rank the homes by when they fail: **in the type** (compile time, zero checks) > **parsed once at a boundary** into a narrower type (one runtime check, in one place, and the result carries its own proof) > **validated at each use** (N checks that must stay in sync) > **documented** (fails in production, at the user). Move each constraint to the earliest home you can afford. This is Ousterhout's "pull complexity downward" applied to types: the type is the lowest layer a constraint can live in.

The countable version: five booleans admit 2⁵ = 32 states; if six are legal, the type claims 32 and you are hand-defending 26. The scale gets away from you immediately — M bits admit 2^M states, so roughly 34 bytes of state already has more configurations than the observable universe has atoms. That is Armstrong's point in *The Mess We're In*: nobody reasons about a system by enumerating its states, so the only move available is to shrink what the system can represent. Illegal states almost always come from modelling a sum as a product — independent fields multiply, variants add. The mechanical moves: mutually exclusive booleans collapse into one enum; a field that is meaningful only when a flag is set moves inside the variant that enables it; ordering constraints become one type per state, with the operation defined only on the state that permits it.

Two stopping rules. Encode only the constraints a plausible caller would get wrong *and* that are cheap to express — types nobody can read are their own tangle. And on a public API this is a genuine trade: adding a field is compatible, adding a variant breaks exhaustive matches, so you buy safety now with evolution cost later.

## Reuse is not free — the boundary on "fold in"

Question 4 defaults to folding in, and that default has an edge. Armstrong lists *reuse* among the reasons software got harder, against an earlier world whose advantages included "no reuse of code," "complete control," and being "understandable in its entirety." His accounting is in responsibility, not lines: *I reuse X in program P, I ship P to a customer, the customer reports an error in P, **I am responsible*** — you buy the function and pay in liability, and liability doesn't transfer. So folding in is right where you own both sides and wrong where you don't. Inside a trust boundary it removes duplication; across one it buys that removal with coupling to something you can't change and must still answer for.

Two claims from the same talk are worth carrying alongside it. Complexity is infectious rather than additive — "bad code contaminates good code," which Armstrong rates the single thing to check before taking a job; a bolt-on shim is therefore not inert, and neither is the module it leans against. And entropy falls only when something forces deletion: early Unix discarded unused programs because the disk was small, natural selection by scarcity. Nothing plays that role now — storage, history, and context are all cheap — so deletion pressure has to be supplied deliberately or it doesn't exist.

## When to actually add a new abstraction

Question 2 of the gate says compose first. The hard case is when you can't. Add a new flag, type, or layer only when the behavior genuinely can't be expressed by composing what exists **and** the new thing pays off: it has to make many future changes shorter, by more than it costs to carry the abstraction and the interactions it opens. A new abstraction used once is a bad trade. One that absorbs a whole class of cases is a good one.

## The judgment the checks can't make for you

- Two redundant paths that reach the *same* result by different routes are cheaper than two that can *diverge*. The duplication check flags both the same; you decide which is the real risk.
- Whether a constraint is worth encoding in types, or is better left to one parse at the boundary, depends on what the language can say cleanly. Name the principle and its local translation; never write a finding that demands another language's idiom.

## Sources

- Rob Pike, [Simplicity is Complicated](https://go.dev/talks/2015/simplicity-is-complicated.slide), dotGo 2015 — features that "cover the space, like a vector basis covering solution space"; orthogonal features that interact predictably.
- Rich Hickey, *Simple Made Easy* — easy versus simple.
- John Ousterhout, *A Philosophy of Software Design* — pull complexity downward; different layer, different abstraction; pass-through methods as the wrong-layer smell.
- Yaron Minsky, *Effective ML* (2010) — make illegal states unrepresentable. Alexis King, *Parse, Don't Validate* (2019) — the method: parse once into a narrower type instead of validating repeatedly.
- Joe Armstrong, [Computer Science — A Guide for the Perplexed](https://files.gotocon.com/uploads/slides/conference_9/360/original/cs_guide_perplexed.pdf), GOTO 2018 — software complexity grows because we build on old stuff; bad code contaminates good code; the reuse-and-responsibility chain; entropy falls only when something forces deletion.
