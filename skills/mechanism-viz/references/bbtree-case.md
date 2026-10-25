# Case study: bbtree

The worked example this skill generalizes. Live: [post](https://bbtree.xiangpeng.systems/post/),
[explorer](https://bbtree.xiangpeng.systems/explorer/). The repos record the reasoning; read them rather than the
minified bundle.

## Source pointers

| What | Where |
|---|---|
| Visualization decision log | [`bbtree/design/10-visualization.md`](https://github.com/XiangpengHao/bbtree/blob/main/design/10-visualization.md) |
| Post text, figure captions, chart and method decisions | [`bbtree/design/14-blogpost.md`](https://github.com/XiangpengHao/bbtree/blob/main/design/14-blogpost.md) |
| Figure generator and motion model | `bbtree/bbtree/vis/figures/src/svg.rs`, one `*.rs` per figure |
| Playback timeline | `bbtree/bbtree/vis/src/timeline.rs` |
| Chart growth timing | `bbtree/bbtree/vis/src/chart_scale.rs` |
| Benchmark rules and harness | [`bbtree-eval/AGENTS.md`](https://github.com/XiangpengHao/bbtree-eval/blob/main/AGENTS.md), `blog/runs.sh`, `integrations/*/RESULTS.md` |

## Mapping

| bbtree | General concept | Your mechanism |
|---|---|---|
| One key's lookup | One instance: a request, message, transaction, job | |
| 64-byte cache line, dots for lines read | The countable cost unit | |
| Miss 100 ns, instruction 0.5 ns, coherence >100 ns | Unit prices that rank the levers | |
| Path cards / memory map / slot table | Structure / resource / state views, one shared hover | |
| Fences and inline keys beside the node | Invariants, shown in place | |
| `inspect` + `trace_many` with a no-op watch | Read-only trace from the real code, zero-cost | |
| `fences.rs` test | Test that pins the viewer to the code | |
| "Lookups worth seeing" | Curated happy, contended, failure/recovery paths | |
| URL params + deterministic build | Seeded, reproducible link | |
| Binary vs linear search over 64 `u64`s | Toy thought experiment, one step per cost unit | |
| `batch-lanes.svg`: core as axis, a lane per task, turns | Lanes per actor, discrete turns, legend defines a turn | |
| `version-lock.svg`: time runs down, readers vs writer | Time-runs-down figure; show which read stands, which retries | |
| Bars grow at one speed | Motion enacts the measured quantity | |
| Marker yellow for bbtree only, grey for competitors | One highlight color for the subject | |
| Guards: author, cross-checking LLMs, fuzz/Verus/DST | How do we know it is correct | |

## Figure captions as specs

Each caption states the setup, what one step means, and the outcome to notice. Paraphrased examples:

- `search-space.svg`: a sorted array spanning 8 cache lines; one step equals one miss. Binary search halves the
  remaining range per step, linear search clears one line per step; the caption gives the miss count for each and
  the array size at which they tie.
- `version-lock.svg`: time flows downward. Two readers and one writer; the reader that finished before the write
  keeps its result, the one that overlapped sees a changed version and retries.

Write the caption before drawing. A figure whose caption cannot name its step unit is not ready.
