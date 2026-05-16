---
name: test-writing
description: Guide test writing and review with focus on observable behavior over implementation. Use when the user asks to write, review, or refactor tests; debates unit vs integration scope; questions whether to mock a dependency; or asks why tests break on refactor. Covers AAA structure, mocking rules (managed vs unmanaged), and the humble-object refactor. See REFERENCE.md for worked examples.
---

# test-writing

Test units of behavior, not units of code. A good test describes one meaningful scenario, observes the result from the system boundary, and survives refactoring.

## Decision tree

```
Complex/important code?
├─ No  → Skip (trivial getters, setters, glue)
└─ Yes → Many dependencies?
    ├─ No  → Unit test the behavior through the public API
    └─ Yes → Can extract logic?
        ├─ Yes → Extract behavior to domain + test thin orchestration separately
        └─ No  → Integration test the end-to-end behavior
```

## What to test

- **Unit**: one business scenario or domain behavior through a public API, not one class by default.
- **Integration**: orchestration, controllers, real databases, real filesystems, and observable system results.
- **Skip**: trivial accessors, private methods (extract instead), implementation details (internal structure, call order).

## Mocking rules

- **Mock unmanaged dependencies** (external systems others depend on): SMTP, message buses, third-party APIs. Mock at the system boundary.
- **Never mock managed dependencies** (resources only your app uses): database, filesystem, in-process domain collaborators. Use the real thing in integration tests.
- **Never mock time** — inject it as a dependency instead of calling `DateTime.Now` / `time.now()`.
- When using mocks, verify only edge interactions that are externally visible and compatibility-sensitive.

## Test structure (AAA)

```
// Arrange: set up inputs
// Act:     execute ONE operation
// Assert:  verify the observable outcome
```

- One behavior per test; multiple assertions are acceptable when they describe the same outcome.
- Keep Act to one line when possible. Multiple Act lines often signal poor API encapsulation or multiple behaviors.
- No conditionals or loops in tests.
- Name tests in plain English, with underscores for readability: `User_login_fails_with_invalid_password`.

## Style preference (best → worst)

1. **Output-based**: `result = add(2, 3); assert result == 5`
2. **State-based**: `cart.add(item); assert cart.count == 1`
3. **Communication-based** (use sparingly): `verify(service.send, once)`

## Red flags

- Test duplicates production logic → use hardcoded expectations.
- Test breaks on refactor → coupled to implementation, not behavior.
- Coverage % as the goal → use coverage only as a negative signal for untested areas.
- Mocking the database → use a real instance.
- Test maps one-to-one to a class or method → reframe around the scenario a domain expert would recognize.
- Testing private methods → extract to a class with its own public API.

## Quality bar

A good test has: **protection** (catches real bugs), **refactoring resistance** (survives implementation changes), **speed** (ms for unit), **clarity** (one obvious failure reason).

A bad test is worse than no test — it locks in the wrong shape.

## Deeper material

- [REFERENCE.md](REFERENCE.md) — humble-object refactor, three-context database pattern, worked examples.
