---
name: blog-review
description: Review a technical blog draft and report what loses its reader, ordered by cost. Use when asked to review, critique, give feedback on, or tighten a draft blog post, article, newsletter issue, or engineering essay, or to 审稿 / 看看这篇. Do NOT use for READMEs, guides, comments, or commit text (use write-docs), for design docs, or to write a post from scratch.
---

# blog-review

Read as the one target reader, who can stop at any sentence. Report the three to five findings that cost that reader most, then the rest. Give suggestions, not rewrites: feedback is always contradictory and the author picks what to act on.

## Procedure

1. Before reading closely, write three lines from the draft alone: the target reader (more specific than "developers"), the post's one claim in one sentence, and what this reader cannot get from the docs or an LLM. A line you cannot fill is finding #1.
2. Read once straight through as that reader, tracing the circulation: after each paragraph, write one line on the reader's mental map — what they now hold (the parts and how they connect), what this paragraph added or changed, and what they still carry unresolved. Mark every place you would stop, reread, or call BS. Then read the title, the last sentence of the intro, and the ending against each other and against the claim.
3. Classify the draft: argument, how-to or explainer, or chronological investigation (bug hunt). The class picks the opening and structure checks below.
4. Run the passes top down. A post-level defect costs more than any sentence. Sentence-level checks run only where you actually stalled; this is not a copy-edit.
5. Verify what you can: run the commands, check numbers against the linked source, check API names. Say which you ran and which you only read.

## Passes

- **Post.** Is the claim in the title, and does the body deliver what the title promises? Does the title name the most interesting result? Is it clear in the first screen who the post is for? Is there one takeaway, or is non-critical detail burying it? The one kill signal: the post only compiles what the docs or an LLM already say, with no first-hand experience, tradeoff, or corner the docs skip.
- **Opening.** Draw the line where the intro ends; if you cannot find it quickly, the reader cannot. Inside it: shared context, then a turn (*but*), then the problem as condition plus cost that answers "so what?", then the point as the intro's last sentence, carrying the words the body repeats. Does the first paragraph assume what only the author knows? A scene-setting anecdote is a finding when it delays information, not when it delivers it. A post about an event (release, incident, announcement) that opens by recapping it: does the mechanism the reader needs to judge it come first? For a cold reader the event is the example, not the premise. **Bug hunt:** invert the default. Withhold the fix, build suspense, but mark the fix with its own heading for skippers.
- **Path.** Walk the reader's route like a house tour: what they see first, and what they must already hold to read each next part. A cold reader needs the map before any room: the problem, the two to four ideas, one overview; a post that opens on mechanism, chronology, or code before that is a finding. At each paragraph, ask what the reader is wondering now and whether this paragraph answers it; a paragraph answering a later question moves. Count what the reader carries unused: an undefined term, a figure label explained later, a number used sections on; three or four at once is a finding. One name per concept: a renamed concept reads as a second one, and a coined name where the field or the source has a term ("isolation shell" for sandbox, "control group" for baseline) is a lookup the reader cannot do. A prior system the argument leans on gets a link at first mention. A detour before the main part (a version diff before the protagonist) drops momentum: fold it into a collapsible block or a margin note, do not cut it. Skippable caveats, inferences, and pointers go in the margin, not on the route. Read the findings off the circulation trace from step 2: a paragraph that adds nothing to the map, an open item that never resolves, a map that contradicts the title, or a question the reader holds at the end that the post never answers.
- **Structure.** Read only the title and headings: do they tell the story in order? Read only each section's point sentence: is that an outline? Where does momentum drop? Length cuts both ways: tangents and detail that does not serve the claim go; a missing step, the evidence for a claim, or the "why" of a decision must come back. An ending that only summarizes is a finding; it should leave the reader something to do, try, or think about. **Bug hunt:** most of the words belong to the investigation, including dead ends; a closing lesson that generalizes from the specific bug is expected.
- **Evidence.** Every superlative and claim has its number, snippet, screenshot, or link. "Much faster" is a finding: how much? Where nothing was measured, a back-of-envelope number with its assumption stated beats the adjective. A source paraphrased where the reader needs its words, or quoted with no sentence after it saying what it means or leaves out, hides what the author added. Code and commands are complete enough to run and were run as shown. Benchmarks state setup and acknowledge bias. Objections and "it depends" cases this reader will raise are answered somewhere. Terms are defined at first use for this reader.
- **Voice.** Flag what reads as AI-written or AI-edited: the mean of all opinions, balanced to nothing, the sharpest claim toned down. Readers leave on suspecting it. *Obviously*, *clearly*, *undoubtedly* make readers think the opposite; a flat universal with no hedge is itself an intensifier; a stack of hedges reads as defensive padding. Trying too hard: memes, forced jokes, AI images. A deadpan or casual tag (*Fine.*, *lol*, a one-line shrug) after a summary instead of reasoning reads as glib; only the mechanism above it earns the shrug. Casual and clinical are both fine; inconsistent register is not.
- **Sentences, only where you stalled.** First seven or eight words: a character as subject and a verb reached? Each sentence opens on what the previous one ended with? The sentence openers in a passage name a small set of topics? Tap the last three or four words: do they deserve stress? A subject longer than seven or eight words holding a nominalization? *Which* and *that* clauses chained past the main clause?

## Do not flag

A passive or nominalization that keeps the topic string or points back at the previous sentence. Established terms (*load balancer*, *garbage collection*). Repeated subjects; variety is not a goal. A short lead-in phrase. A mechanism or toy model before the news; that is information, not scene-setting. *There is* or *it is* used to push new information to the end. A deliberate periodic sentence or negative ending. A hedge where the author is in fact uncertain. Casual grammar in a bug-hunt post. A topic someone else already covered. Length by itself.

## Output

```
[§ heading or ¶N] "<quoted sentence, heading, or title>"
  Reader: <stops | gets lost | cannot trust | rereads | cannot run | asks "so what?">
  Instead: <one concrete suggestion, at most one rewritten sentence>
```

- Open with the circulation trace: one line per paragraph where the map changes, `[¶N] holds: … · new: … · open: …`. It shows the route, not a summary of the content.
- Then the top three to five findings, labeled as such, then the rest grouped by pass. No finding without a quoted location.
- No score, no praise lead, no padding toward a count. A short review of a tight draft is the correct output.
- Close with two lines: the claim you read versus the title, and the question this reader still has after the last paragraph.
- Never rewrite the post. If the point is buried, say so; a from-scratch rewrite is the author's move.

Exact test wording, qualifications, and sources: [references/REFERENCE.md](references/REFERENCE.md).
