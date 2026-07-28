# CONTEXT.md Format

`CONTEXT.md` records the shared language of a repository or bounded context. It should explain project-specific concepts that are easy to misuse, not general programming ideas or implementation details.

## Template

```md
# {Context Name}

{One or two sentences describing this context and why its language matters.}

## Language

**Canonical Term**: One sentence defining what the concept is.
_Avoid_: ambiguous synonym, overloaded synonym

## Relationships

- A **Term A** owns one or more **Term B** records.
- A **Term C** references **Term A** by ID only.

## Example Dialogue

> **Developer:** "When does a **Term A** become visible to users?"
> **Domain expert:** "Only after **Term B** is approved."

## Flagged Ambiguities

- "account" was used for both **Customer** and **User**. Resolution: use **Customer** for the buyer and **User** for the login identity.
```

## Rules

- Prefer one canonical term and list words to avoid when ambiguity would matter.
- Keep definitions to one sentence.
- Define what the concept is, not every operation performed on it.
- Include relationships when they clarify ownership, cardinality, lifecycle, or boundaries.
- Include only project-specific language. Exclude generic concepts like retries, queues, controllers, DTOs, or timeouts unless the project gives them a special domain meaning.
- Use subheadings when several clusters of terms emerge.

## Single vs Multiple Contexts

For most repositories, create one root `CONTEXT.md`.

For multiple bounded contexts, create a root `CONTEXT-MAP.md`:

```md
# Context Map

## Contexts

- [Ordering](./src/ordering/CONTEXT.md): receives and tracks customer orders
- [Billing](./src/billing/CONTEXT.md): generates invoices and processes payments

## Relationships

- **Ordering -> Billing**: Ordering emits order events consumed by Billing.
```

When `CONTEXT-MAP.md` exists, read it before editing context docs. If the current topic could belong to more than one context, ask which context owns it.
