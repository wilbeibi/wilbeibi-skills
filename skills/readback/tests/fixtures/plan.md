# Cache design discussion

A short plan with the shapes the reader has to survive: headings, nested lists,
a table, a quote, code, and inline `formatting`.

## Goals

- Bound memory use.
  - Per-tenant ceiling, not a global one.
  - Evict on pressure, not on a timer.
- Keep expiry legible to operators.

## Policy

Cache entries expire after 24 hours. The same sentence appears twice in this
document on purpose, so anchoring has to distinguish them by position.

| Layer   | TTL  | Eviction |
|---------|------|----------|
| edge    | 60s  | LRU      |
| region  | 1h   | LFU      |
| origin  | 24h  | none     |

> Cache entries expire after 24 hours. Operators asked for one number they can
> recite, not a policy they have to compute.

### Invalidation

```python
def evict(entries, now, ttl=86400):
    """Drop entries past their ttl. Deliberately long enough to fold."""
    keep = []
    for entry in entries:
        if now - entry.written_at < ttl:
            keep.append(entry)
        else:
            entry.release()
    return keep
```

Escaped markup such as <b>bold</b> and an autolink-looking string
https://example.com/not-linkified must render as text, not as HTML.

## Open questions

1. Does the edge layer need its own eviction metric?
2. Who owns the per-tenant ceiling?
