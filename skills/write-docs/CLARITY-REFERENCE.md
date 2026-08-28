# Clarity rules — rationale and sources

This skill borrows a small, useful subset of ASD-STE100 without turning all developer prose into controlled English.

## What transfers well

[ASD-STE100 Issue 9](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf) separates procedural and descriptive writing. Its relevant rules include:

- one technical name for one item and consistent wording for repeated actions;
- active voice unless the actor is unknown;
- direct verbs for actions;
- conditions before commands and one instruction per procedural sentence;
- 20-word procedural sentences and 25-word descriptive sentences;
- one topic per paragraph.

These constraints help most where ambiguity changes an action. A 1996 study of 175 aircraft maintenance technicians found significantly better comprehension for Simplified English, especially on difficult workcards and for non-native speakers. A 1998 study of 41 non-native students found no significant overall difference, but a trend favoring readers with lower English proficiency. The evidence supports targeted use, not a universal prose style.

- Study: <https://journals.sagepub.com/doi/10.1177/154193129604000502>
- Related study: <https://open.library.ubc.ca/soa/cIRcle/collections/ubctheses/831/items/1.0078187>

## Why natural mode exists

Developer prose also needs voice and flow. Google's developer documentation guide recommends common contractions and allows passive voice when the actor is unknown, irrelevant, or intentionally de-emphasized.

- Contractions: <https://developers.google.com/style/contractions>
- Active voice and exceptions: <https://developers.google.com/style/voice>
- Consistent terminology: <https://developers.google.com/tech-writing/one/words>

Thus, strict rules apply to actions and safety. Natural prose keeps the same terminology and factual discipline without a controlled vocabulary or mechanical cadence.

## What this skill rejects

- The approximately 900-word STE dictionary: software needs precise domain terms and identifiers.
- Universal word substitutions: the project's established term is safer than a generic “simpler” synonym.
- Global bans on contractions, semicolons, phrasal verbs, or passive voice.
- American spelling when the project has a different house style.
- A composite “slop score”: weighted surface features do not measure truth, completeness, or comprehension.

The checker was inspired by the experiment kit for [“The cure for AI slop is a 1986 aircraft manual”](https://github.com/woosal1337/blog/tree/main/videos/ep01-the-cure-for-ai-slop), but is an independent implementation. The upstream experiment is useful directional evidence, not a quality benchmark: it tests six tasks and scores outputs with rules that overlap the intervention.
