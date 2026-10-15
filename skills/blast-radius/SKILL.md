---
name: blast-radius
description: Trace what a change could break beyond its diff and verify the assumptions its safety depends on. Use for "blast radius", "what could this break", or indirect compatibility and lifecycle risks. Use code-review for a general diff review.
---

# blast-radius

Find the failure a caller search misses, then run the cheapest check that could disprove the safety claim.

## Workflow

1. **Anchor the change.** Identify the base and candidate, read the diff, and state the changed behavior. Include effects hidden behind an unchanged interface. Done when the review has a named revision and scope.
2. **Name the safety assumptions.** Write the concrete facts that would make the risky paths safe. There may be several independent facts; do not force the change into one explanation. For each, name an input or state that would falsify it.
3. **Follow the indirect effects.** Trace only the relevant seams: persisted data, serialized fields, another process or language, flags, caches, teardown, scheduling, retries, or downstream consumers. Check a dependency's pinned version and local patches before relying on its behavior. Done when each material risk has a real path through the code, with locations.
4. **Try to break the assumptions.** Prefer a small script importing production code, an existing harness, or an isolated run of the app. Check the result and side effects, rather than a copy of the algorithm. Preserve the command and output. Done when each consequential assumption has evidence or an explicit gap.
5. **Bound the verdict.** State which inputs, versions, and runtime conditions the proof covers. Separate confirmed failures, checked paths, and unverified possibilities. Passing one case does not prove a universal claim.

## Evidence

Label the evidence for each safety assumption:

| Evidence | What it establishes |
|---|---|
| Source traced | The pinned implementation supports the claim; runtime behavior remains untested. |
| Executed | Real code was exercised with named inputs and checked outputs. |
| App reproduced | The relevant path was exercised in the running app, including the effect at issue. |
| Unproven | A required dependency, environment, or check was unavailable. Name the gap. |

A plausible explanation without a code path is a hypothesis. Avoid invented consumers and numeric probabilities without data. A search with no hits narrows the search result, not the set of possible external consumers.

## Scope and proof

- Preserve the requested review or fix scope. A review finding does not authorize a repair.
- Run proofs against isolated scratch state where possible. Live services, data, external writes, and restricted actions retain the session's approval requirements.
- Keep exploratory scripts in the task's scratch directory unless a durable artifact is requested or a regression earns a place in the project suite.
- When an unsafe check cannot run, report the assumption as unproven and give the smallest next check. Do not mutate the environment to make the claim true.

## Output

Lead with the material finding or the bounded verdict. Include the behavior change, safety assumptions with evidence labels, confirmed failure paths with code locations, checks that cleared specific risks, and remaining gaps. Link proof artifacts or include a short command and result. Omit empty categories.

Adapted from [pstack/blast-radius](https://github.com/cursor/plugins/blob/850d7f2e9f5e55dff7eb00a0a479337fe79eb22f/pstack/skills/blast-radius/SKILL.md), under the [MIT license](LICENSE.pstack).
