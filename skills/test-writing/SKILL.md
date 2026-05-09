---
name: test-writing
description: Guide test writing and review with focus on observable behavior over implementation. Use when the user asks to write, review, or refactor tests; debates unit vs integration scope; questions whether to mock a dependency; or asks why tests break on refactor. Covers AAA structure, mocking rules (managed vs unmanaged), and the humble-object refactor. See REFERENCE.md for worked examples.
---

# test-writing

Test observable behavior, not implementation. Tests must survive refactoring.

## Decision tree

```
Complex/important code?
├─ No  → Skip (trivial getters, setters, glue)
└─ Yes → Many dependencies?
    ├─ No  → Unit test (pure logic, public API)
    └─ Yes → Can extract logic?
        ├─ Yes → Extract to domain (unit) + thin controller (integration)
        └─ No  → Integration test
```

## What to test

- **Unit**: domain logic, pure functions, business rules — through public APIs.
- **Integration**: controllers, real databases, real filesystems.
- **Skip**: trivial accessors, private methods (extract instead), implementation details (internal structure, call order).

## Mocking rules

- **Mock unmanaged dependencies** (external systems others depend on): SMTP, message buses, third-party APIs. Mock at the system boundary.
- **Never mock managed dependencies** (resources only your app uses): database, filesystem, in-process domain collaborators. Use the real thing.
- **Never mock time** — inject it as a dependency instead of calling `DateTime.Now` / `time.now()`.

## Test structure (AAA)

```
// Arrange: set up inputs
// Act:     execute ONE operation
// Assert:  verify ONE outcome
```

- One logical assertion per test.
- No conditionals or loops in tests.
- Name tests as plain English: `User_login_fails_with_invalid_password`.

## Style preference (best → worst)

1. **Output-based**: `result = add(2, 3); assert result == 5`
2. **State-based**: `cart.add(item); assert cart.count == 1`
3. **Communication-based** (use sparingly): `verify(service.send, once)`

## Red flags

- Test duplicates production logic → use hardcoded expectations.
- Test breaks on refactor → coupled to implementation, not behavior.
- Coverage % as the goal → measure behavior coverage instead.
- Mocking the database → use a real instance.
- Testing private methods → extract to a class with its own public API.

## Quality bar

A good test has: **protection** (catches real bugs), **refactoring resistance** (survives implementation changes), **speed** (ms for unit), **clarity** (one obvious failure reason).

A bad test is worse than no test — it locks in the wrong shape.

## Deeper material

- [REFERENCE.md](REFERENCE.md) — humble-object refactor, three-context database pattern, worked examples.
