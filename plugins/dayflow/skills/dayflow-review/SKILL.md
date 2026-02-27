---
name: dayflow-review
description: Query and analyze Dayflow time tracking database. Generate daily or weekly summaries, productivity insights, and timeline reports. Use when reviewing time usage or trends.
---

# Dayflow Review

## Summary
Use this skill to summarize Dayflow time tracking data from the local SQLite DB. Keep queries focused and filter soft deletes.

## Details

Database:
- `~/Library/Application Support/Dayflow/chunks.sqlite`
- WAL files: `chunks.sqlite-wal`, `chunks.sqlite-shm`
- Always filter soft deletes: `WHERE is_deleted = 0`

Key tables:
- `timeline_cards`: main activity blocks (`day`, `start_ts`, `end_ts`, `title`, `category`, `subcategory`, `metadata`)
- `journal_entries`: daily intentions/reflections

Python connection:
```python
# /// script
# dependencies = []
# ///
import sqlite3
from pathlib import Path

path = Path.home() / "Library" / "Application Support" / "Dayflow" / "chunks.sqlite"
conn = sqlite3.connect(str(path), timeout=5.0)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA busy_timeout = 5000")
```

Response filtering:
- If you dump JSON for external tools, use `jq` to narrow fields.
- For small queries, filter in SQL or Python and avoid extra dependencies.

## Reference

Duration helpers:
```sql
(end_ts - start_ts) / 60.0 AS minutes
ROUND((end_ts - start_ts) / 3600.0, 2) AS hours
```

Daily category summary:
```sql
SELECT category,
  ROUND(SUM(end_ts - start_ts) / 3600.0, 2) AS hours
FROM timeline_cards
WHERE day = date('now') AND is_deleted = 0
GROUP BY category
ORDER BY hours DESC;
```

Weekly totals:
```sql
SELECT category,
  ROUND(SUM(end_ts - start_ts) / 3600.0, 2) AS hours
FROM timeline_cards
WHERE day >= date('now', '-7 days') AND is_deleted = 0
GROUP BY category
ORDER BY hours DESC;
```

Focus sessions (30+ min work):
```sql
SELECT day, start, end, title,
  ROUND((end_ts - start_ts) / 60.0, 1) AS duration_min
FROM timeline_cards
WHERE category = 'Work'
  AND is_deleted = 0
  AND (end_ts - start_ts) >= 1800
ORDER BY duration_min DESC;
```
