# test-writing — Reference

Worked examples and patterns referenced from `SKILL.md`.

## Humble object refactor

When a method mixes domain logic with dependencies, split it so the domain part is unit-testable and only the orchestration needs integration tests.

**Before** — complex method, hard to test:
```
service.changeEmail(id, email) {
  user = db.get(id)
  if (external.validate(email)) {
    user.email = email
    db.save(user)
  }
}
```

**After** — domain logic is pure, controller is thin:
```
// Domain (unit test)
User.changeEmail(email, validator) {
  if (validator.isValid(email)) {
    this.email = email
    return EmailChanged(email)
  }
}

// Controller (integration test)
Controller.changeEmail(id, email) {
  user = db.get(id)
  event = user.changeEmail(email, validator)
  db.save(user)
  bus.publish(event)
}
```

Now the interesting branching lives in `User.changeEmail` and runs in milliseconds. The controller test only proves the wiring.

## Three-context database pattern

For DB integration tests, use three separate contexts/transactions to avoid false positives from caching or unflushed writes:

```
// Arrange context
db1.insert(user)

// Act context
db2 = newContext()
controller.update(userId, db2)

// Assert context
db3 = newContext()
assert db3.get(userId).email == expected
```

Clean data at the **start** of the test, not the end — a failed test should leave evidence in the DB.

## When to refactor instead of testing

If code is "high complexity + many dependencies", don't add integration tests around it. Extract the logic into a domain object (unit-testable) and leave behind a thin controller (integration-testable). The test pyramid is downstream of the design.

## When mocking communication is OK

Communication-based assertions (`verify(service.send, once)`) are acceptable for the boundary between your system and an unmanaged dependency you can't observe directly — e.g., asserting an outbound webhook fired. They're a code smell anywhere else, because they couple the test to the call sequence.
