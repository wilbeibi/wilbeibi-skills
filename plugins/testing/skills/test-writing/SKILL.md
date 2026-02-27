---
name: test-writing
description: Guide effective, maintainable test writing that enables sustainable software growth. Covers unit vs integration tests, mocking rules, and anti-patterns.
---

# Test Writing Skill

## Purpose
Guide effective, maintainable test writing that enables sustainable software growth.

## Core Philosophy

**Goal**: Enable sustainable project growth, not just find bugs.

**Key Rule**: Test observable behavior, not implementation details. Tests must survive refactoring.

## What to Test

### ✅ Unit Test
- Domain logic with high complexity, few dependencies
- Pure functions, business rules, calculations
- Observable behavior through public APIs

### ⚠️ Integration Test  
- Controllers (low complexity, many dependencies)
- Database operations (use real DB)

### ❌ Don't Test
- Trivial getters/setters
- Private methods (extract to new class if complex)
- Implementation details (internal structure, call order)

### 🔧 Refactor First
- High complexity + many dependencies
- Extract logic to domain (unit test) + thin controller (integration test)

## Test Structure (AAA Pattern)

```
// Arrange: Set up inputs
// Act: Execute ONE operation  
// Assert: Verify ONE outcome
```

- One logical assertion per test
- No conditionals/loops in tests
- Name as plain English: "User_login_fails_with_invalid_password"

## Mocking Rules

### Only Mock Unmanaged Dependencies
**Unmanaged** = External systems others depend on
- ✅ Message buses, SMTP, external APIs
- Mock at system boundaries

### Never Mock Managed Dependencies
**Managed** = Resources only your app uses
- ❌ Databases (use real instances)
- ❌ Filesystems  
- ❌ Domain collaborators (test together)

## Test Style Preference

1. **Output-based** (best): `result = add(2, 3); assert result == 5`
2. **State-based**: `cart.add(item); assert cart.count == 1`
3. **Communication-based** (minimal): `verify(service.send, once)`

## Database Testing

**Pattern**: Use 3 separate contexts/transactions
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

Prevents false positives from caching. Clean data at test START.

## Red Flags

- Testing private methods → Extract or test via public API
- Test duplicates production logic → Use hardcoded expectations
- Coverage metric as target → Focus on behavior coverage
- Mocking database → Use real DB
- Test breaks on refactoring → Coupled to implementation
- `DateTime.Now` → Inject time as dependency

## Refactoring Pattern (Humble Object)

**Before**: Complex method with dependencies
```
service.changeEmail(id, email) {
  user = db.get(id)
  if (external.validate(email)) {
    user.email = email
    db.save(user)
  }
}
```

**After**: Separate concerns
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

## Decision Tree

```
Complex/important code?
├─ No → Skip (trivial)
└─ Yes → Many dependencies?
    ├─ No → Unit test
    └─ Yes → Can extract logic?
        ├─ Yes → Extract + unit test domain
        └─ No → Integration test
```

## Quality Checklist

Good tests have:
- **Protection**: Catches real bugs in critical paths
- **Refactoring resistance**: Survives implementation changes
- **Speed**: Milliseconds for unit tests
- **Clarity**: One clear failure reason

## Remember

- Test behavior, not implementation
- Good tests survive refactoring  
- Bad tests worse than no tests
- Mock only at system boundaries
