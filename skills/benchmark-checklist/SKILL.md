---
name: benchmark-checklist
description: Check whether a measured performance claim supports a comparison or decision. Use when running benchmarks, reporting a measured speedup or regression, or choosing between implementations from timing results. Do NOT use for interpreting published benchmarks without running them or for general debugging.
---

# benchmark-checklist

Test the sentence the measurement is supposed to support.

## Before measuring

Write the proposed claim with its metric, workload, and scope. Read the harness to see what it times, counts, awaits, and ignores. Define a correctness check independently of the timing result.

Inspect machine load and resource limits. If competing work cannot be avoided, interleave the alternatives and report the interference; do not stop unrelated processes.

## Check the result

| Question | Required evidence |
|---|---|
| **What limits it?** | Profile separately from reported timing runs. Map the bottleneck to code or a resource; check that the load generator is not the bottleneck. |
| **Is the comparison fair?** | Comparable versions, data, builds, cache state, concurrency, and production settings. Tune avoidable configuration bottlenecks before recommending an implementation. If tuning is out of scope, bound the claim to the configurations tested and leave the adoption decision open. |
| **Is the magnitude possible?** | Check bandwidth, core capacity, and the affected share of total time. Removing 10% of a run saves at most 10% of its time, about a 1.11x speedup. A result beyond a physical or arithmetic bound needs investigation. |
| **Did it succeed?** | Count failures, retries, timeouts, and non-success responses. Validate actual outputs; fast rejection is not fast completion. |
| **Does it repeat?** | For a comparison, start with at least five runs per side in alternating order, unless the user sets a smaller budget. Record warmup, raw results, median, and range. Mark the conclusion inconclusive when the budget or variation cannot support the claimed difference. |
| **Does it affect the user?** | Measure the relevant end-to-end path with realistic data and concurrency. State a microbenchmark's share of the whole; without that check, keep the claim at microbenchmark scope. |
| **Did the work happen inside the timer?** | Observe completion counts or effects: consumed iterators, awaited work, returned bytes, written rows, or used results. Setup, asynchronous tail work, caching, and no-ops can invalidate the timed region. |

For an explicitly requested ballpark, one run is enough. Still verify successful output and work inside the timer, label it a single run, and do not turn it into a winner recommendation. A choice between alternatives is a comparison.

## Decision

- **Faster / slower:** the successful, comparable runs support a difference beyond observed variation; explain the limiting work.
- **No measurable difference:** the valid experiment cannot distinguish the alternatives at its observed resolution.
- **Inconclusive:** correctness, completion, comparability, repetitions, or the proposed explanation is unresolved. Name the missing evidence.

Distinguish elapsed-time reduction from throughput increase. For example, 100 ms to 80 ms is 20% less time and, for serial work, 1.25x throughput. Preserve units and the statistic being compared.

## Output

Lead with the verdict and its scope. Give the main before/after number with units, run count, median and range, correctness/work counts, and bottleneck evidence. Link the harness and raw results when available. State limits that could change the decision; do not generalize a configuration result into an implementation ranking.

Adapted from [pstack/benchmark-checklist](https://github.com/cursor/plugins/blob/850d7f2e9f5e55dff7eb00a0a479337fe79eb22f/pstack/skills/benchmark-checklist/SKILL.md), under the [MIT license](LICENSE.pstack).
