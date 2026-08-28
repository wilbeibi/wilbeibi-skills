# Developer guides and runbooks

Write task-oriented documentation that lets a reader act without inventing missing state, commands, or recovery steps.

## Workflow

1. Classify the document: tutorial, how-to, runbook, migration, deprecation, or API usage guide.
2. Verify every command, parameter, version boundary, prerequisite, and expected result against its source.
3. Name the starting state and the observable end state.
4. Put the shortest safe path first. Move alternatives and background after it.
5. Run procedural blocks in **strict** mode and explanations in **natural** mode.
6. Test commands when the environment permits. Mark untested examples explicitly.

## Task shape

- State prerequisites before the first step. Include versions and permissions only when they change the path.
- Use numbered steps for ordered work. Give one action per step.
- Put a condition before its instruction so an inapplicable step is easy to skip.
- Show the expected result after a step when the reader needs it to decide whether to continue.
- For destructive or stateful work, state the affected scope, checkpoint, failure signal, and rollback.
- Keep conceptual explanation near the decision it supports. Link to reference material instead of interrupting the task.

## Artifact differences

- **Tutorial:** choose one supported path and teach a complete first success. Do not turn it into an option catalog.
- **How-to/API guide:** assume a specific goal; include inputs, output shape, errors, and the common integration path.
- **Runbook:** optimize for a stressed operator. Put diagnosis before repair, preserve evidence, and make stop conditions explicit.
- **Migration/deprecation:** identify affected users, old and new behavior, deadline or version boundary, exact replacement, and rollback or coexistence limits.

## Final check

- A reader can tell whether the guide applies before changing anything.
- Commands and examples use real names and current syntax.
- Each step has enough context to execute, but no unrelated theory.
- Failure and recovery paths are explicit where they affect safety or data.
- The document promises no behavior that the implementation does not provide.
