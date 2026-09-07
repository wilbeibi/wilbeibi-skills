# sherlock — method, sources, and where the maxims break

Read this when the loop in [SKILL.md](SKILL.md) feels wrong for the case, or when you want to know why a rule is there.

## Why this shape

Most bad investigations are framing failures, not collection failures: you can run forty tools against a question and produce a confident answer to a different one. So the first step rewrites the ask until it has a stopping condition and a written *no*. The second is observation before theory, because once a theory exists, facts get bent to fit it. The third is several theories at once with a consistency matrix, because the natural mode — pick the likeliest story, look for support — always succeeds; support is easy to find for any plausible story, which is why the matrix counts *inconsistencies* and ignores support. The casebook exists because an investigation outlives a context window and a dead branch re-entered is the most expensive mistake available.

## The Holmes maxims, and their failure modes

| Maxim | The rule it encodes | Where it breaks |
|---|---|---|
| "It is a capital mistake to theorize before one has data" | Steps 2 before 3 | Pure observation has no end; frame the question first so you know which data. |
| "You see, but you do not observe" | Log every detail, including absences ("the dog did nothing in the night-time") | Detail without grading is noise; the grade is what makes a clue usable later. |
| "The more outré and grotesque an incident, the more carefully it deserves to be examined" | The odd detail is the lever | Sometimes the odd detail is a second, unrelated cause. Residuals must be named, not forced into the verdict. |
| "When you have eliminated the impossible, whatever remains, however improbable, must be the truth" | Kill by inconsistency, keep the survivor | Only valid if the hypothesis list was exhaustive and each kill rested on hard evidence. Both fail routinely — hence `H0: none of the above` and "an improbable survivor is a signal to re-check both". |
| "Reason backward" from effects to causes | Start at the failure and walk causality upstream; in reverse-engineering, from constraints to the designs they force | Backward chains compound uncertainty; re-anchor each hop to a confirmed clue. |
| "There is nothing more deceptive than an obvious fact" | Check the clue everyone agrees on | — |

## Method sources

- **Analysis of Competing Hypotheses** (Richards Heuer, *Psychology of Intelligence Analysis*, ch. 8; short walkthrough: https://isc.sans.edu/diary/22460; a worked matrix: https://sroberts.github.io/2016/12/12/rnc-hack/). Eight steps: enumerate hypotheses; list evidence and assumptions; build the matrix with consistent / inconsistent / not applicable per cell; drop rows that are consistent with everything; conclude by trying to *disprove*; run a sensitivity check on the few clues the verdict rests on; report every hypothesis and why each was rejected; name future indicators. The loop's steps 3-6 are these, minus the ceremony for small cases.
- **Key Assumptions Check** (CIA *Tradecraft Primer*, https://www.cia.gov/resources/csi/static/Tradecraft-Primer-apr09.pdf). List every working assumption behind the judgment, why it is held, what changes if it is wrong, and mark it supported / caveated / unsupported. This is the casebook's Assumptions table.
- **Admiralty grading** (NATO source-reliability letter × information-credibility number), as applied in useosint's `investigate-anything` skill (https://github.com/useosint/skills). Its three traps are ours: circular corroboration, stale data presented as current, and tool output treated as evidence.
- **Agans, *Debugging*, nine rules** (summary: https://dwheeler.com/essays/debugging-agans.html): understand the system; make it fail; quit thinking and look; divide and conquer; change one thing at a time; keep an audit trail; check the plug; get a fresh view; if you didn't fix it, it ain't fixed. "Quit thinking and look" is the cure when theories multiply without new clues; the audit trail is the casebook; the last rule is why a debug verdict needs the fix to remove the failure and its revert to restore it.
- **Zeller, scientific debugging** (*Why Programs Fail*; https://queue.acm.org/detail.cfm?id=1217270): a logbook row of hypothesis → prediction → experiment → observation → conclusion, repeated until the hypothesis cannot be refined. The casebook's Tests table has an `expected` column so the prediction is written before the run.
- **Julia Evans, debugging manifesto** (https://jvns.ca/blog/2022/12/08/a-debugging-manifesto/): inspect, don't squash; trust nobody and nothing; it's probably your code; there's always a reason.
- **Allspaw on Five Whys** (https://www.kitchensoap.com/2014/11/14/the-infinite-hows-or-the-dangers-of-the-five-whys/): a linear why-chain assumes one cause and tunnels. The matrix is the antidote — two causes show up as no single column clean.
- **Differential diagnosis**: enumerate, order by base rate ("hoofbeats → horses") and by cost of being wrong, rule out with the cheapest discriminating test. This is where "boring theory first" and "test by what splits the live set" come from. Bayes in prose: the best next test is the one whose outcome you can least predict across the live theories.
- **Anthropic prompting guidance** (https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) recommends, verbatim, developing "several competing hypotheses", tracking confidence in progress notes, and updating "a hypothesis tree or research notes file to persist information and provide transparency". Tree of Thoughts (arXiv 2305.10601) is the same loop stated as search: branch, self-evaluate, backtrack. Reflexion (arXiv 2303.11366) is the "why was this branch wrong" line on a dead theory.

## Reverse-engineering from public signals

Sources, strongest first. Every clue gets a date; a verdict about *now* needs at least one clue from now.

1. **Your own observation.** DevTools/HAR traces, response headers, redirect chains, ID formats (UUIDv7 vs Snowflake vs ULID says something about the ID service), rate-limit and cache headers, JS bundle names and source maps, error messages at the edges (send a bad request; error text names frameworks and internal services), latency under load, behaviour differences between two accounts, regions, or plans, and interrogating the product itself when it has a conversational surface.
2. **Primary engineering publications.** Engineering blog, conference talks, papers, patents, public SDK and CLI source, changelogs, status-page components and incident postmortems (a postmortem names the internal services that failed).
3. **Administrative disclosures.** Subprocessor lists and DPAs (which clouds and vendors), SOC 2 / security pages, DNS TXT verification records (every SaaS that verified the domain), CSP headers (every third-party origin the front end talks to), `.well-known/` files, job posts with dates (stack, scale numbers, "we are migrating from X to Y").
4. **Secondary.** StackShare, BuiltWith, forum and HN threads with employees, LinkedIn titles, analyst write-ups.
5. **Marketing.** Product pages, press releases. Graded low until backed by 1 or 2.

What `scripts/fingerprint.sh` output tends to imply — leads, not verdicts:

| Signal | Suggests |
|---|---|
| CNAME to `*.vercel-dns.com`, `*.netlify.app`, `*.pages.dev`, `*.herokudns.com`, `*.elb.amazonaws.com`, `*.azurewebsites.net` | hosting / edge provider |
| `server: cloudflare`, `cf-ray`, `cf-cache-status` | Cloudflare in front; origin hidden |
| `x-served-by: cache-*`, `x-cache`, `via: 1.1 varnish` | Fastly / Varnish CDN |
| `x-amz-cf-id`, `x-amz-*` | CloudFront / AWS |
| `x-vercel-id`, `x-vercel-cache` | Vercel; `vary: rsc, next-router-*` means Next.js app router |
| `server: envoy`, `x-envoy-*` | service mesh or Envoy gateway |
| `x-runtime` | Rails; `x-powered-by` names the framework when not stripped |
| `alt-svc: h3` | QUIC-capable edge |
| TLS issuer Let's Encrypt vs a corporate CA; `subject: CN=*.example.com` | managed certs vs owned PKI |
| MX at Google / Microsoft; SPF includes | mail and marketing vendors |
| many `*-domain-verification` TXT records | the SaaS vendor list, dated by nothing — corroborate |
| `/.well-known/openid-configuration` 200 | an OIDC issuer at this host |
| `robots.txt` disallow paths | admin, staging, API, and internal paths worth a look; sitemap size hints at catalog scale |

Worked examples of the case done well, and the signals they leaned on:

- Inferring OpenAI's inference stack from pricing tiers (QoS queues), prompt-caching docs (prefix-hash routing), and dated job posts, with confidence stated per claim and an explicit "still unknown" list: https://www.linkedin.com/pulse/openai-doesnt-run-vllm-i-spent-days-inference-stack-from-krish-gupta-gzy3c
- A company's stack from subprocessor lists, status-page components, historical job posts, DNS TXT, CSP headers, and third-party domains in network calls: https://bloomberry.com/blog/how-to-find-any-companys-tech-stack-without-paying-for-it/
- Cursor's LLM client from a proxy trace, with the proxy chain reconstructed and the unknowns (the Tab model) named rather than guessed: https://www.tensorzero.com/blog/reverse-engineering-cursors-llm-client/
- ChatGPT memory from interrogation probes and cross-account comparison, with reproducible links: https://www.shloked.com/writing/chatgpt-memory-bitter-lesson
- A gym app's API via mitmproxy: envelope format, versioned subdomain, UA requirement: https://dev.to/dtterastar/i-pointed-claude-at-mitmproxy-and-it-reverse-engineered-my-gym-apps-api-1a4h

## Prior-art skills, and what was taken

- **obra/superpowers `systematic-debugging`** (https://github.com/obra/superpowers): "no fixes without root-cause investigation"; log at component boundaries before hypothesizing; after three failed fixes stop and question the architecture with the human; a red-flag list of rationalizations ("quick fix for now", "one more attempt"). Taken: the three-strike budget and boundary logging. Not taken: its single-hypothesis rule, which is deliberately anti-branching.
- **garrytan/gstack `/investigate`**: confirm a suspected root cause with a temporary log or assertion that must fire; never say "this should fix it"; completion statuses DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT. Taken: the temporary-assertion test and the honest "unanswerable" close.
- **labrinyang/team-ochestractor `competing-hypotheses`**: one agent per hypothesis, each reporting evidence for *and against*; a devil's advocate asking "root cause or masked symptom?"; winning and eliminated hypotheses written to a file "to prevent future anchoring". Taken: fan-out that returns marks not verdicts, and recording the eliminated.
- **markusstrasser ACH skill** (https://github.com/markusstrasser/skills): "your job is not to confirm"; an always-present artifact / measurement-error hypothesis; `[SOURCE]` vs `[INFERENCE]` tags; residual-uncertainty section. Taken: the premise-is-wrong theory, observed-vs-inferred labels, residuals and falsifier in the verdict.
- **leynos `hypothesis-debugging`** (https://github.com/leynos/agent-helper-scripts): a Popperian plan doc — per hypothesis a claim, a prediction, a falsification table with expected negative result, then execution order cheapest-decisive-first and termination criteria. Taken: predicts-what-others-don't, the expected column, and the stopping condition in the frame.
- **majiayu000 `bayes-reasoner`**: mandatory `Other` bucket; rank tests by expected information. Taken in prose as `H0` and "test by what splits the live set". Not taken: the calculator.
- **neolabhq FPF `propose-hypotheses`** (https://github.com/neolabhq/context-engineering-kit): abduction → deduction → induction ladder with hypotheses promoted L0 → L1 → L2 on disk. Taken: durable state on disk. Not taken: the 600k-token framework and subagent choreography.
- **tinyfish `tech-stack-detective`**: five parallel sources; high confidence = three or more independent sources. Taken: the independence rule inside the grades.
- Registry filler (`sherlock-review`, `bug-detective`, `error-detective`): observe → deduce → eliminate → conclude with nothing underneath. Not taken.
