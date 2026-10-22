# blog-review reference

Three sources, layered. Post, opening, structure, evidence, and voice checks come from
[writethatblog.substack.com](https://writethatblog.substack.com/) (35 posts read 2026-10-13: the
synthesis posts and 25 interviews). Paragraph and sentence checks come from Williams & Bizup,
*Style: Lessons in Clarity and Grace*, 12th ed. (2016), lessons 3 to 10 and 12. Counts are the
number of distinct posts that state a rule. Quotes under 40 words. The event-post opening, quote-then-gloss,
labeled estimates, and unearned-shrug checks come from Matt Levine's *Money Stuff* (Bloomberg;
57 issues close-read 2026-06 to 10, 247 sections); see [Money Stuff](#money-stuff).

Williams' ranking, which the passes follow: readers want characters as subjects even more than
actions as verbs; a passage's cohesion "trumps the clarity of individual sentences"; and "readers
are more likely to judge as clear any unit of writing that opens with a short segment that they can
easily grasp and that frames the longer and more complex segment that follows." So review
beginnings first: the intro, each section's opener, each paragraph's opener, each sentence's opener.

## Post level

- Single point, stated in the title (6 posts). "I like to have each post make a single point (and
  ideally to express that point in the title)." [goedecke](https://writethatblog.substack.com/p/sean-goedecke-on-technical-blogging)
- One takeaway; non-critical detail buries it (3). "If you dump everything into the blog post,
  readers won't discover the highlights." [glauber-costa](https://writethatblog.substack.com/p/glauber-costa-on-technical-blogging)
- Reader named, more specific than "developers" (4). "Is it immediately clear who this article is
  for and why the reader should care?" [reviewing-llm](https://writethatblog.substack.com/p/reviewing-your-blog-post-llm)
- Offers what docs or an LLM cannot: first-hand experience, the why of a tradeoff, a corner the
  docs skip (9). "not just 'rehashing documentation' that the AI chatbots these days can do very
  well" [tanel-poder](https://writethatblog.substack.com/p/tanel-poder-on-technical-blogging)
- Title sets no false expectation and names the most interesting term or result in the body (3).
  [reviewing-llm](https://writethatblog.substack.com/p/reviewing-your-blog-post-llm)
- Kill signal: pure compilation with no author perspective is the one case the blog says to cut.
  Already-covered-by-someone-else is explicitly not a reason: "Not every post has to be
  groundbreaking." [gunnar-morling](https://writethatblog.substack.com/p/gunnar-morling-on-technical-blogging)
- Writing outside what the author knows (5). "Don't pretend to be someone you're not. It's bad
  writing and people can sniff it out." [thorsten-ball](https://writethatblog.substack.com/p/thorsten-ball-on-technical-blogging)

## Opening

Williams, Lesson 7. Skeleton: [prelude] → shared context → problem (condition + cost) → solution
or main point. The six-step audit, quoted:

1. "Determine whether you are posing a practical or conceptual problem. Do you want readers to do
   something or to think something?" Explainers, investigations, and postmortems are conceptual:
   the condition is "a statement of what we do not know."
2. "Draw a line after your introduction. If you cannot quickly locate the end of your
   introduction, neither will your readers."
3. "Divide the introduction into its three parts: shared context + problem + solution/main
   point/claim. If you cannot quickly make those divisions, your introduction is likely to seem
   unfocused."
4. "Make sure the first word of the first sentence after the shared context is *but*, *however*,
   or some other word indicating that you will challenge that shared context."
5. "Divide the problem into two parts: condition and cost." Then: "Does the cost appropriately
   answer *So what?*" For a conceptual problem the cost is the larger question the small one
   serves.
6. "Underline your solution/main point/claim. This should appear at the end of the introduction
   in its stress position, and should state the key themes that the rest of your paper will
   develop."

Symptom of a topic-only intro: the reader "may shrug and ask, *So what?*"

Do not flag: skipping shared context when readers know the subject; cost before condition when
readers know the problem; condition alone when readers see the cost unaided. A prelude is
optional.

Blog-side:

- First screen states the author's relation to the topic and what the reader gets (3).
  "Does the beginning... tell the reader what to expect and why my perspective on this topic is
  interesting?" [reviewing-llm](https://writethatblog.substack.com/p/reviewing-your-blog-post-llm)
- Missing context paragraph (2). "You're always missing a paragraph and you assume that I know way
  more than I do. Give me more context, please!" [hanselman](https://writethatblog.substack.com/p/scott-hanselman-and-mark-downie-blogging)
- Scene-setting anecdote that delays information (2). "Refuse the magazine-style layout."
  [antirez](https://writethatblog.substack.com/p/antirez-on-technical-blogging). Williams agrees.
- Bug-hunt inversion (1): "For most blog posts, we recommend sharing the TL;DR early on... Not
  here!" Withhold the fix, build suspense, but "mark 'the fix' with a nice prominent heading so
  they can skip ahead to the smoking gun." Casual grammar is accepted in this pattern only.
  [bug-hunt](https://writethatblog.substack.com/p/the-bug-hunt-blog-post-pattern)
- Failed openings the blog names: a strawman of the opposing view (willison had to apologize); a
  post pitched to the wrong audience (poder took it down).

## Structure

Williams, Lessons 6 and 8:

- Title the paragraph: "For a paragraph more than five or six sentences long, underline the
  sentence that you think best introduces or frames the rest of the paragraph. If you can't do that
  quickly, your paragraph probably has a problem. If you can, circle the important words in the
  sentence. Those words should sound like a title for the paragraph." Skip short or transitional
  paragraphs.
- Point sentence closes the opening segment of the document, each section, and each long
  paragraph. Read only the point sentences: "such 'point' sentences constitute the outline of your
  document." A point-last paragraph inside a well-framed section is fine.
- Theme repetition: the key words of the point sentence recur through the body.
- Order: name the principle (chronological, coordinate, logical), then "read it through to see
  whether you have organized it simply as a narrative of your thinking. If you have, consider
  revising." A bug-hunt post is the sanctioned exception.
- Conclusion mirror: restate the point, answer "so what?" as a benefit, answer "now what?".
  A conclusion that only summarizes is a finding.

Blog-side:

- Title plus headings alone tell the story, phrased consistently (4). "If the reader just scans the
  title, headings, and subheadings, will they get a good idea of what this article actually
  covers?" [reviewing-llm](https://writethatblog.substack.com/p/reviewing-your-blog-post-llm)
- Narrative arc and where momentum drops (5). "have a story with a beginning, a middle, and an end.
  It doesn't have to be super long" [atwood](https://writethatblog.substack.com/p/jeff-atwood-on-technical-blogging)
- Reverse outline: one idea per section, in an order that builds a reasoning (3). [antirez]
- Short (7 posts): "Keep it short, keep it snappy. Edit twice as much as you write."
  [charity-majors](https://writethatblog.substack.com/p/charity-majors-on-technical-blogging)
- Thorough (7 posts): "If you worry that you might be adding too many technical details, err on
  the side of more. Readers can always skip" [bug-hunt]. Reconciliation: cut what does not serve
  the one point; never cut a step the reader must reproduce, the evidence for a claim, or the why
  of a decision. Report both directions.
- Scanning aids in at most the three most valuable places (2). "Name 3 or fewer places"
  [reviewing-llm]
- Ending gives something to do, try, or contemplate (3). "Or does it just stop?" [reviewing-llm]
- Investigation posts: about 80% of the words on the investigation; generalize the specific bug
  into a broader lesson at the end (2). [bug-hunt]

## Evidence

- Every claim or superlative backed by a number, snippet, screenshot, or link (7). Posts "look less
  legit if they use vague phrasing like 'our system is now much faster.' Readers will immediately
  think 'Yeah, but how much faster?'" [bug-hunt]
- Code and commands complete and run as shown (5). "Even one wrong fact can throw off a reader new
  to a technology or area." [dan-moore](https://writethatblog.substack.com/p/dan-moore-on-technical-blogging)
- Failures, dead ends, tradeoffs shown (4). "Be brutally honest about all your failures." [bug-hunt]
- The why of decisions, not only the what (4). "The 'why' of tradeoffs is a deeper level of
  understanding" [tanel-poder]
- Expert reader finds a missed edge case (5). "someone will call you out on it every time if you get
  anything wrong" [preston-thorpe](https://writethatblog.substack.com/p/preston-thorpe-on-technical-blogging)
- Benchmarks: reproducible setup, bias acknowledged (2). Authors are "guilty until proven innocent."
  [glauber-costa]
- Objections and "it depends" answered (3). Find "where they might call BS"
  [cantrill](https://writethatblog.substack.com/p/bryan-cantrill-and-friends-on-blogging)
- Terms and acronyms defined at first use for the target reader (2).
- Later corrections stay visible in the post, not silently rewritten (2). [matt-butcher]

Williams, Lesson 12, for passages about a mistake, risk, cost, or failure: list the subject of
every clause. Is the responsible agent or the affected reader ever a subject, or are alarming
actions nominalized and passive (*failure*, *is left unengaged*) while reassuring ones are active
first person? "Our choice of subjects determines not just whether our writing is clear but also
whether it is honest or deceptive." Do not flag kindness in bad news.

## Voice

- AI-sounding text (10 posts). "The mean of all opinions. Uncontrasting." Survey of 668
  developers: 78% leave on suspecting AI, 71% avoid the author afterwards, 98% prefer the author's
  imperfect writing; "Any hint of AI generated text makes everything in the article suspect."
  [dev-reaction](https://writethatblog.substack.com/p/dev-reaction-to-ai-blog-posts)
- AI editing toned down the sharpest claim (3). "AI edits tend to tone down the most interesting
  and controversial aspects of your writing" [goedecke]
- Reads like documentation, no person behind it (7). "don't mask your true personality in an
  attempt to sound 'more professional'" [cantrill]
- Trying too hard (4). "Cool it with the memes and AI-generated images." [thorsten-ball]
- Partisan or incendiary where confident (4). "it undermines your purpose" [atwood]
- Register consistent within the post (2). Clinical ([sam-rose](https://writethatblog.substack.com/p/sam-rose-on-technical-blogging)) and casual (bug-hunt) are both endorsed.

Williams, Lesson 9, on hedges and intensifiers:

- "When most readers read a sentence that begins with something like *obviously, undoubtedly, it
  is clear that, there is no question that*... they reflexively think the opposite."
- "The most common intensifier... is the absence of a hedge." A flat universal (*all*, *every*,
  *never*) reads as aggressive; "if you state a claim moderately, readers are more likely to
  consider it thoughtfully."
- A stack of hedges (*seems... some... could... possibly*) is "mealy-mouthed." Beyond these two
  rules the book says to trust your ear; do not impose a hedge count.
- Concise, not terse: cutting 205 words to 51 "stripped away its garrulous charm, a tradeoff that
  many readers would reject." Flab is a finding; voice is not.

## Sentences

Run these only on sentences where the reader stalled. All quotes are Williams.

- **First seven or eight words** (L3). "Ignoring short (four- or five-word) introductory phrases,
  underline the first seven or eight words in each sentence. Then ask two questions: Did you
  underline any abstract nouns as simple subjects? Did you underline seven or eight words before
  getting to a verb? If you answer yes to either, you should probably revise." Fix: find the
  character and action hidden in the nominalization; make them subject and verb.
  Do not flag: a short subject pointing back (*These arguments all depend on...*); a nominalization
  standing in for *the fact that*; the verb's object (*accepted her request*); a term so familiar
  it is "a virtual character" (*garbage collection*, *replication*).
- **Who is doing what** (L4). Recover characters from possessives, *of* and *by* phrases, and
  adjectives. "choose the most specific characters you can find"; for instructions, *you*.
  Do not flag an abstraction that is the subject of a sustained story (*the scheduler*, *the
  cache*), only an unfamiliar abstraction "surround[ed] with a lot of other abstractions."
- **Passive is fine** when the actor is unknown or irrelevant, when it lets the sentence begin
  with the shorter or more familiar bundle, or when it keeps a consistent point of view. Make it
  active when the verb names the writer's own act (*the terms must be defined* → *we define*).
- **Old before new** (L5). The last few words of one sentence set up the first few of the next.
  This outranks the two tests above: "a passage's overall cohesion trumps the clarity of
  individual sentences."
- **Topic string** (L5). "Underline the first seven or eight words of every sentence in a passage,
  stopping when you hit a verb... Imagine giving the passage a title. The words in it are likely to
  name important topics." Do not flag repeated topics: "do not vary your subjects for the sake of
  variety... your readers may be grateful for the repetition." Most writers change topics too
  often.
- **Throat-clearing** (L5). Flag a stack of connector + attitude + time + place before the subject,
  not a single short one. Count *thus, therefore, however, moreover* per page; each *but* must
  mark a real turn.
- **Tap test** (L6). "Read your sentence aloud and, as you reach the last three or four words, tap
  your finger hard as if emphasizing them in a speech. If you tap on words that do not deserve
  strong emphasis, look for words that do. Then put those words closer to the end." Trim the end,
  move metadiscourse left, move the new or technical term right. Do not flag a deliberate negative
  ending.
- **Noun strings** (L4). Three or more nouns in a row from the author's own coinage: reverse the
  order and add prepositions. Keep established compounds (*load balancer*) and unpack the rest.
- **Concision** (L9). Meaningless words (*kind of, actually, basically, really, various*); doubled
  words (*any and all, each and every*); implied words (*past history, period of time*); phrase for
  word (*the reason for* → *why*, *in the event that* → *if*, *prior to* → *before*); negatives for
  affirmatives (*not many* → *few*, *not include* → *omit*), worst with passives; "try deleting
  every adverb and every adjective before a noun, and then restore only those that readers need."
  Redundant metadiscourse: topic announcement (*This section introduces...*) and attribution
  (*has been observed to occur*). "Almost everything you write needs some."
- **Shape** (L10). Length is not the symptom. Point first in a short main clause. "Underline whole
  subjects. If you find a subject longer than seven or eight words that includes a nominalization,
  especially as the simple subject, try turning the nominalization into a verb and using a
  character as its subject." Nothing between subject and verb or verb and object. Sprawl test:
  "If that reader hesitates, stumbles over words, or runs out of breath before getting to the end
  of a sentence, so will someone reading your writing silently"; proxy is *which/that/who* clauses
  chained after the main clause. *And... and... and* joining claims whose real relation is
  *because* or *but*. Do not flag a deliberate periodic sentence, a short interruption, or a short
  leading *if/when/although* clause carrying known information.
- **Elegance** (L11) is never a finding. Offer a balanced or climactic ending only for a sentence
  that already passes everything above, and only once per post.

## Review conduct

- Lead with the three to five highest-impact issues from the target reader's view (3 posts).
  "3-5 most impactful things" [reviewing-llm]
- Read title, intro, and conclusion against each other: "How well does the blog post deliver what
  the title and introduction promise?" [reviewing-llm]
- "What questions might [target reader] have after reading?" [reviewing-llm]
- Feedback is contradictory; the author chooses (4). "Listen to all feedback, but be picky about
  what you act upon." [sam-rose]
- Feedback worth giving "genuinely points out ways your post could be more clear, or more
  accurate, or more complete" [eric-lippert](https://writethatblog.substack.com/p/eric-lippert-on-technical-blogging)
- Limit the review to what blocks the post. Eight interviewees say publish imperfect: "Aim to hit
  publish while you are still actively unhappy with what you have written"
  [willison](https://writethatblog.substack.com/p/simon-willison-on-technical-blogging)
- The LLM's role is adversarial reader, not editor: "to check that the argument I'm making does
  not have any embarrassing holes" [willison]. Hence suggestions, never a rewrite.
- Williams' golden rule, the final test on any suggestion: "what really counts... is not what
  writers think they have put into a passage but what readers get out of it." Would the author,
  standing where this reader stands, accept the passage as is?

## Money Stuff

Counts are sections of 150 words or more, hand-coded by six readers on one rubric.

- Mechanism before the news (~170/247). A principle or toy model comes first; the news arrives
  300 to 1,300 words in, and setup scales with section length. "The basic business of finance is
  slicing up cash flows." The best case: the news turns out to be the extreme the hypothetical
  already predicted. This is information, so do not flag it as a delaying anecdote.
- Quote, then translate (most sections that quote). A 100 to 300 word quote, then one sentence
  saying what the source does not: "it never says Susquehanna *lost* $71.4 million."
- Labeled toy numbers. "Those numbers are made up, and I don't know the actual threshold". The
  label makes a mechanism concrete; it is not cover for vagueness.
- Endings add something new; about one in eight sections closes by restating. No summary
  paragraph, no call to action.
- Unearned shrug: every reader flagged it independently as the move imitators get wrong. "Fine."
  and "Sure?" land only after 500 or more words of mechanism make the absurdity visible.
- Headlines: median five words, a plain claim naming the lead story in the author's restatement,
  often understated ("Bank of America Missed Some Bad Guys"); section labels stay flat.
  Already covered by the Post pass.
- Does not transfer to a monthly blog: "around here" callbacks and running gags need a daily
  reader who remembers yesterday. Restate in one line and link.
