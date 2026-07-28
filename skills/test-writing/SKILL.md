---
name: test-writing
description: Guide tests toward observable behavior instead of implementation. Use when writing or reviewing tests, choosing test scope or mocks, or fixing brittle tests.
---

# test-writing

Test behavior through the smallest useful boundary, not implementation shape.

## Routing

1. Trivial glue/getters? Skip.
2. Single meaningful behavior, few dependencies? Unit test through the public API.
3. Orchestration, real I/O, controller/database/filesystem behavior? Integration test.
4. Many dependencies but extractable logic? Extract domain behavior and test orchestration thinly.

## Rules

- One test = one scenario a domain expert would recognize.
- Prefer output-based tests, then state-based tests; use communication mocks only for compatibility-sensitive external calls.
- Mock unmanaged dependencies: SMTP, queues, third-party APIs. Do not mock managed dependencies like your DB, filesystem, or in-process domain collaborators.
- Never mock time; inject a clock.
- Arrange, Act, Assert. Keep Act to one operation when possible.
- Multiple assertions are fine when they describe one outcome.

## Red Flags

- Test duplicates production logic instead of hardcoding expected results.
- Test breaks on refactor because it checks internals, private methods, call order, or class layout.
- Coverage percentage becomes the goal.
- Database/filesystem behavior is mocked away.
- Conditionals or loops appear inside the test.

## Quality Bar

A good test has protection, refactoring resistance, speed appropriate to its layer, and one obvious failure reason. A bad test is worse than no test because it locks in the wrong shape.

See [REFERENCE.md](REFERENCE.md) for humble-object refactors, database test patterns, and worked examples.
