# ADR Format

ADRs record decisions whose rationale is likely to matter later. They should be short by default.

## When To Offer An ADR

Offer an ADR only when all three are true:

1. The decision is costly to reverse.
2. A future maintainer would not understand the choice from the code alone.
3. Real alternatives existed, and the selected option reflects a tradeoff.

Skip ADRs for obvious choices, temporary experiments, easy-to-change details, or decisions with no meaningful alternative.

## Location And Naming

Store ADRs under `docs/adr/` using sequential numbering:

```text
docs/adr/0001-use-manual-sql.md
docs/adr/0002-split-billing-context.md
```

Scan existing ADRs, increment the highest number, and use a short lowercase slug.

## Minimal Template

```md
# {Decision Title}

{One to three sentences explaining the context, decision, and rationale.}
```

## Optional Sections

Add these only when they clarify the decision:

```md
---
status: accepted
---

## Considered Options

- Option A
- Option B

## Consequences

- Non-obvious downstream effect.
```

Good ADR candidates include architectural boundaries, storage choices, integration patterns, deliberate deviations from standard practice, compliance constraints, or rejected alternatives that are likely to come up again.
