# How it actually works

This is the long version. If you want the short version, read the [README](README.md). If you want to understand what happens when you run this skill, how the agent thinks, and what the lab looks like after 30 experiments, keep reading.

---

## The idea

You have a codebase. Something about it could be better. Maybe your API is slow. Maybe your tests are flaky. Maybe your document parser misses edge cases.

You know what "better" looks like. You can measure it. But you don't know which changes will get you there.

Normally you'd sit down, try something, run the tests, check the results, try something else. Repeat until you're happy or tired.

This skill makes your AI agent do that loop for you. You tell it what to optimize, how to measure it, and what files it can touch. Then you walk away.

The agent tries things, measures, keeps what works, reverts what doesn't. You come back to a log of everything it tried and a codebase that's better than when you left.

---

## What happens when you start

You drop `researcher.md` into your agent (Claude Code, Cursor, whatever reads markdown). Then you say something like:

> "I want to optimize the p99 latency of this API endpoint."

The agent doesn't start hacking immediately. First it interviews you:

| Question | Your answer |
|----------|------------|
| What's the goal? | Reduce p99 latency |
| How do we measure it? | `./bench.sh \| grep p99` outputs a number in ms |
| Lower is better? | Yes |
| What files can I touch? | Anything in `src/api/` and `src/db/` |
| What's off-limits? | Don't change the public API contract. Don't add dependencies. |
| How long can one experiment take? | 5 minutes max |
| When do we stop? | When p99 < 50ms, or after 40 experiments, or when I say so |

The agent repeats this back to you. You confirm. Then it builds the lab.

---

## The lab

The agent creates two things:

1. **A git branch** — `research/reduce-p99`
2. **A `.lab/` directory** — gitignored, survives all reverts

Git manages your code. `.lab/` manages the experiment history. They're independent. This matters because the agent will be reverting code constantly, but the experiment log must survive.

```
.lab/
├── config.md          Everything you agreed on
├── results.tsv        Every experiment, one row each
├── log.md             Narrative: what was tried, why, what happened
├── branches.md        Branch registry (if the agent forks)
└── parking-lot.md     Ideas for later
```

Then the agent runs your benchmark with zero changes. This is **experiment #0** — the baseline.

> **Baseline:** p99 = 142ms

Now it knows what "before" looks like. The loop begins.

---

## The loop

```
       ┌───────────────────────────────┐
       │                               │
       ▼                               │
  ┌─────────┐                          │
  │  THINK  │  Read history, analyze,  │
  │         │  form hypothesis         │
  └────┬────┘                          │
       │                               │
       ▼                               │
  ┌─────────┐                          │
  │  TEST   │  Commit, run, measure    │
  │         │  Keep or revert          │
  └────┬────┘                          │
       │                               │
       ▼                               │
  ┌─────────┐                          │
  │ REFLECT │  Log result, check       │
  │         │  convergence signals     │
  └────┬────┘                          │
       │                               │
       └───────────────────────────────┘
```

---

### Think

The agent reads the experiment history. What's been tried? What worked? What didn't? Are there patterns?

It checks convergence signals (more on those later). Then it forms a hypothesis:

> "The N+1 query in `getUserOrders` is probably the bottleneck. If I batch the order fetches, p99 should drop."

Sometimes the agent decides it doesn't need to run code yet. Maybe it can reason about the problem first. These are **thought experiments**. The agent analyzes, writes a conclusion in the log, and moves on. No code change, no run.

This matters because 10 minutes of good analysis can prevent 5 wasted experiments.

### Test

The agent makes changes to the code. Before running anything, it commits:

```
git commit -m "experiment: batch order fetches in getUserOrders"
```

This commit is the safety net. If the experiment fails, the agent reverts to here.

Then it runs the benchmark. Redirects all output to `run.log` so it doesn't flood its own context window. Waits for the result.

**If it crashes:**
- Typo or missing import? Fix, retry once.
- Fundamental problem (OOM, missing dependency)? Log, revert, move on.

**If it succeeds:**

| Outcome | Action |
|---------|--------|
| Metric improved | **Keep.** Advance the branch. |
| Metric equal but code is simpler | **Keep.** Simplification win. |
| Metric equal or worse | **Discard.** `git reset --hard HEAD~1` |
| Metric didn't improve but result is informative | **Interesting.** Agent decides. |

> p99 = 118ms. That's better than 142ms. **Keep.**

### Reflect

The agent writes an entry in `log.md`:

```markdown
## Experiment 1 — Batch order fetches in getUserOrders

**Branch:** research/reduce-p99
**Type:** real | **Parent:** #0
**Hypothesis:** N+1 query is the bottleneck, batching should reduce p99
**Changes:** replaced loop with batch query in getUserOrders
**Result:** p99 = 118ms (was 142ms baseline) — new best
**Status:** keep
**Insight:** The N+1 was real. 17% improvement from one change.
            Check if similar pattern exists in getOrderDetails.
```

And a row in `results.tsv`:

```
1  research/reduce-p99  #0  a1b2c3d  118.00  mem:220MB  keep  45  batch order fetches
```

Then the loop repeats.

---

## What 30 experiments look like

After a few hours, `results.tsv` might look like this:

| # | Branch | Parent | Metric | Status | Description |
|---|--------|--------|--------|--------|-------------|
| 0 | research/reduce-p99 | - | 142.00 | keep | baseline |
| 1 | research/reduce-p99 | #0 | 118.00 | **keep** | batch order fetches |
| 2 | research/reduce-p99 | #1 | 121.00 | discard | add Redis cache for users |
| 3 | research/reduce-p99 | #1 | - | thought | cache won't help, reads are already fast |
| 4 | research/reduce-p99 | #1 | 108.00 | **keep** | connection pooling |
| 5 | research/reduce-p99 | #4 | 106.00 | **keep** | reduce pool idle timeout |
| 6 | research/reduce-p99 | #5 | 105.00 | discard | prepared statements |
| 7 | research/reduce-p99 | #5 | 103.00 | discard | switch to raw SQL |
| 8 | research/reduce-p99 | #5 | 97.00 | **keep** | batch getOrderDetails (same N+1 pattern) |
| 9 | research/reduce-p99 | #8 | 94.00 | **keep** | reduce JSON serialization overhead |
| 10 | research/reduce-p99 | #9 | - | thought | remaining latency is network, not code |

**What happened here:**

- **#2** added a Redis cache. Didn't help. Discarded, code reverted.
- **#3** was a thought experiment. The agent realized caching wasn't the right direction. No code changed, but the reasoning is in the log.
- **#8** found the same N+1 pattern in another method. The agent recognized it from experiment #1 and applied the same fix. That's the agent learning from its own history.
- **#10** is a thought experiment where the agent concludes: the easy wins are done, remaining latency is network.

> **Result:** p99 went from 142ms to 94ms. 34% improvement. 5 keeps, 3 discards, 2 thought experiments.

---

## Convergence detection

This is the part that prevents the agent from grinding the same idea forever.

After every experiment, the agent checks a table of signals:

| Signal | What it means | What to do |
|--------|--------------|------------|
| 5+ discards in a row | Current approach is exhausted | Pivot completely |
| Metric plateau (<0.5% over 5 keeps) | Small tweaks are done | Go radical |
| Same code area modified 3+ times | Over-optimizing one spot | Look elsewhere |
| Alternating keep/discard | Conflating variables | Isolate them |
| 2+ timeouts in a row | Approach too expensive | Scale down |
| Results contradict theory | Your model is wrong | Rethink from scratch |
| Branch stagnating, other thriving | Wrong branch | Switch or combine |

These aren't hard rules. They're signals. The agent reads them, considers the history, and decides. Sometimes it pivots. Sometimes it ignores a signal because it has a strong hypothesis.

The skill gives it freedom to choose.

---

## Branching

Sometimes the agent wants to explore two different directions from the same starting point.

```
Experiment #5 (p99 = 106ms)
├── Branch A: optimize database queries further
└── Branch B: try a completely different caching strategy
```

It can fork. Create a new branch from any successful experiment, register it in `.lab/branches.md`, and keep exploring. The experiment history tracks which branch each experiment belongs to and which experiment it was forked from.

The agent considers results from **all branches** when thinking. If Branch B finds something great, the agent can combine it with Branch A's wins.

---

## Thought experiments

Not every hypothesis needs a benchmark run. If the agent can reason about whether an approach will work, it should.

| Real experiment | Thought experiment |
|----------------|-------------------|
| Changes code | No code changes |
| Git commit + run | Analysis only |
| Produces a metric | Produces a conclusion |
| Logged as keep/discard | Logged as thought |

An agent that just tries everything wastes cycles. An agent that thinks first, then tests selectively, converges faster. The skill treats both as equal. Both produce knowledge. Both get logged.

---

## When it stops

The agent stops when one of these happens:

1. Target metric reached (p99 under 50ms)
2. Experiment count limit hit (40 experiments)
3. You tell it to stop
4. **Default: it never stops.** It keeps going until you interrupt.

When it stops, it writes `.lab/summary.md`:

- Total experiments (real + thought)
- Best metric vs baseline
- Top 3 most impactful changes
- What failed and why
- Ideas it didn't get to (from the parking lot)

---

## What you're left with

```
Your project/
├── src/                  Code with only the improvements (failures reverted)
├── .lab/
│   ├── config.md         What you agreed on
│   ├── results.tsv       Open it in any spreadsheet
│   ├── log.md            Reads like a research journal
│   ├── branches.md       The exploration tree
│   ├── parking-lot.md    Ideas for next time
│   └── summary.md        The highlights
└── .gitignore            .lab/ stays local
```

The code changes are real commits. The history is clean because failed experiments got reverted. Only the improvements survive in git. The full story (including failures) lives in `.lab/`.

---

## What this works on

Anything where you can say "run this" and "check this number."

| Domain | Run command | Measure command |
|--------|-----------|----------------|
| API performance | `wrk -t4 -c100 http://localhost:3000/api` | `grep p99` |
| Test suite speed | `npm test` | `time` output |
| Bundle size | `npm run build` | `stat -f%z dist/main.js` |
| Parser accuracy | `./run-tests.sh` | `grep "pass rate"` |
| Document comparison | custom script | custom score |

It also works **without a run command**. If your metric is qualitative ("does this code read better?"), the agent scores against a rubric you define together. Subjective, but consistent rubric + consistent scale = usable signal.

---

## What this doesn't do

It doesn't replace thinking about your architecture. It doesn't magically know what to optimize. It doesn't work well when the metric is noisy or the feedback loop is slow.

It works best when:

- The problem is clear
- The metric is fast to compute
- The search space is wide enough that trying 20 things beats debating which one to try

---

## Try it

One file: [`researcher.md`](researcher.md)

Drop it in. Point your agent at a problem. See what happens.
