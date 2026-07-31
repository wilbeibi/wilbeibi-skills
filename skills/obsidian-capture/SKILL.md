---
name: obsidian-capture
description: Append todos, logs, learnings, and reflections to Obsidian daily or weekly notes, and run the agent's own #agent-todo queue, via scripts/capture.py. Use when asked to add a todo, note something down, log this, capture an idea, set a due date, record a weekly reflection, or list/close the agent's assigned tasks ("看你的 todo", "干活", "what's on your todo list"). Do NOT use for searching notes (use obsidian-search) or for creating standalone long-form notes.
---

# obsidian-capture

One capture = one `scripts/capture.py` call. The script handles everything deterministic — resolves today's daily / this week's weekly note (creates it from the vault template if missing), routes to the right section, fills empty placeholder slots before appending, formats Tasks-plugin dates — so never edit the notes by hand. Needs `$OBSIDIAN_VAULT` and python3 (stdlib only).

## Commands

```bash
scripts/capture.py todo "回 offer 邮件"                    # daily ✅ 其他, due today
scripts/capture.py todo "准备 design review" --must        # daily 🎯 今天必须完成, due today
scripts/capture.py todo "写 freshrss theme" --weekly       # weekly ## Todos, due = today+3d, capped at Sunday
scripts/capture.py todo "读论文" --due friday -p high      # any todo: explicit due + ⏫ priority
scripts/capture.py log "和 recruiter 通话"                 # daily 🪵 Log, timestamped now (--time HH:MM to backfill)
scripts/capture.py learned "TIL 内容"                      # daily 📝 今日记 → 新知:
scripts/capture.py diary "发生的事"                        # daily 📝 今日记 → 新事:
scripts/capture.py fun "有趣的事"                          # weekly ## Something Fun This Week
scripts/capture.py reflect "杠杆" "答案全文"               # weekly Reflections, under the Q: matching the substring
scripts/capture.py done "package 邮件"                     # tick first matching open #agent-todo (today's notes first, then all), appends ✅ date
scripts/capture.py annotate "加 CI" "blocked: 缺权限"      # append a sub-bullet under first matching open #agent-todo

# agent-owned todos (#agent-todo): captured for a later, possibly weaker, agent to execute cold
scripts/capture.py todo "给 skills repo 加 CI" --agent \
  --ctx "context: repo ~/Local/wilbeibi-skills，GitHub Actions 跑 skill lint" \
  --ctx "done-when: push 后 Actions 全绿"
scripts/capture.py agenda                                  # list open #agent-todo due ≤ today + context, file:line (--days 90 default)
```

`--due` accepts `today`, `tomorrow`, `+Nd`, `mon`..`sunday`, `this-week`, `next-week`, `YYYY-MM-DD`, `none` — pass the user's phrase through instead of computing dates yourself. Run `--help` for the rest.

## Judgment (the only part the model decides)

- **Plain todos are the human's; `--agent` ones are yours.** `agenda`/`done`/`annotate` only ever match `#agent-todo` lines, so they can't touch a human todo — but never mark one done without checking it against its own `done-when:`.
- Keep the capture text in the language the user used; don't translate or rephrase.
- "必须 / must / today's deadline / blocking" → `--must`; otherwise a plain todo.
- Daily vs weekly: default daily. Use `--weekly` only when the user says weekly / 本周, or the task is week-scoped with no fixed day. A todo due far in the future still goes in **today's** daily — the Tasks plugin finds it by its 📅 date, not by file location.
- "让 agent 做 / 给 agent 记" → `--agent`. The executor may be a weak model with no conversation history, so the todo must be cold-start executable: `--ctx "context: ..."` with absolute paths/repos/URLs and `--ctx "done-when: ..."` acceptance criteria. Pull specifics from the current conversation; if you can't make it self-contained, ask the user rather than capture a vague one. (The script refuses `--agent` without `--ctx`.)
- The script prints the file, section, and exact line it wrote — relay that as confirmation, and stop. If it errors (unmatched section/question/todo), fix the arguments; don't fall back to hand-editing.
