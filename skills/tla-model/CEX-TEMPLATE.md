# CEX-<NNN>: <property> violated in <cfg>

- Property: <name> (Req R<n>)
- cfg / bounds: <file>, <constants>
- Trace length: <k> states; liveness: stem <a> + loop <b>

## First bad state
Step <i>, action `<Action>(<args>)`. Variables that changed and why that is wrong:
- `x`: 4 → 3 (should never decrease)

## Reachable in the real system?
Map every step to a code event (file:line) and a fault the brief allows.
If any step needs a behavior the code or environment cannot produce, the model is too permissive: the class is spec or assumption, not design.

## Class (pick one)
- [ ] design: the real system can do this; the code or protocol must change
- [ ] spec: the model allows behavior the code cannot produce
- [ ] property: the requirement is stated wrongly (needs user sign-off)
- [ ] config/bounds: constants, constraint, or cfg wiring
- [ ] mapping: event→action or refinement mapping is wrong
- [ ] fairness/assumption: a missing or unjustified environment guarantee

## Change for this round (REQUIRED: exactly one)
Target: model | property | cfg. The edit, and why it removes the cause rather than hiding the symptom.

## Regression
- [ ] This trace replayed and no longer reproduces
- [ ] Whole bounds matrix rerun
- [ ] Mutants for the affected property still KILLED
- [ ] Design class: test, fault injection, or issue created → <link>
