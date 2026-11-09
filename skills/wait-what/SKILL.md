---
name: wait-what
description: Re-pitches the agent's last message after it did not land, with context first, every label explained, and plain short sentences. Use when the user types /wait-what or says the last message was unclear.
disable-model-invocation: true
---

# wait-what

The last message did not land. Re-pitch it and add no new findings.

1. Open with one sentence of context: what we are doing and where it stands.
2. Give the conclusion next, then only the support the reader needs to act on it.
3. Explain every label on first use. An issue or PR number gets a few words on what it is. A decision id, phase, or acronym gets its meaning.
4. Use the project's canonical terms from its glossary, if it has one, and keep one word per concept.
5. Write short sentences as in write-docs strict mode: one idea each, the doer and the verb first. Reply in the user's language and keep code identifiers as they are.

Done when the re-pitch is no longer than the original, or adds only definitions.

Ported from [mattpocock/skills](https://github.com/mattpocock/skills) `wait-what` (MIT), adapted to this repo's conventions.
