<img width="1376" height="768" alt="Gemini_Generated_Image_5z6cxx5z6cxx5z6c" src="https://github.com/user-attachments/assets/02c3c4cd-fe2a-4fcd-b414-29bd84f5a741" />

# Researcher Skill

**One file. Your AI coding agent becomes a scientist.**

[![Latest Release](https://img.shields.io/github/v/release/krzysztofdudek/ResearcherSkill)](https://github.com/krzysztofdudek/ResearcherSkill/releases/latest)
[![License](https://img.shields.io/github/license/krzysztofdudek/ResearcherSkill)](LICENSE)

Drop `researcher.md` into Claude Code, Codex, or any agent. It will design experiments, test hypotheses, discard what fails, keep what works — 30+ experiments overnight while you sleep.

## What it looks like running

> ### Experiment 5 — Parallelize independent test suites
> **Branch:** research/faster-tests · **Parent:** #3 · **Type:** real
>
> **Hypothesis:** Unit and integration suites don't share state. Running them in parallel should cut total time.
> **Changes:** split test config into two parallel jobs in `test.config.ts`
> **Result:** 38s (was 94s baseline, 52s best) — **new best**
> **Status:** keep
>
> **Insight:** Most of the remaining time is in integration tests. Unit tests finish in 6s. Focus on integration from here.

| # | branch | metric | status | description |
|---|--------|--------|--------|-------------|
| 0 | research/faster-tests | 94s | keep | Baseline |
| 1 | research/faster-tests | 71s | keep | Remove redundant setup/teardown |
| 2 | research/faster-tests | 74s | discard | Shared test fixtures |
| 3 | research/faster-tests | 52s | keep | Mock external HTTP calls |
| 4 | research/faster-tests | - | thought | DB reset is slow but tests need clean state, skip for now |
| 5 | research/faster-tests | **38s** | **keep** | Parallelize independent test suites |

*Example is simulated. The skill works on any codebase — run it and share your real results.*

**Same loop, different problems:**
- `npm run build` takes 40s → agent gets it to 18s
- prompt returns wrong format 30% of the time → agent gets it to 3%
- API p99 is 200ms → agent finds the bottleneck and cuts it to 80ms
- document parser misses edge cases → agent improves match rate from 74% to 91%

## How it works

The agent interviews you about what to optimize, sets up a lab on a git branch, and works autonomously. Thinks, tests, reflects. Commits before every experiment, reverts on failure, logs everything.

It forks branches to explore divergent approaches. Detects when it's stuck and changes strategy. Keeps going until you stop it or it hits a target.

Generalizes [autoresearch](https://github.com/karpathy/autoresearch) beyond ML. Supports thought experiments, non-linear branching, qualitative metrics, convergence signals, and session resume.

All experiment history lives in an untracked `.lab/` directory. Git manages code. `.lab/` manages knowledge.

**Want the full walkthrough?** Read the [guide](GUIDE.md). It walks through a complete example from start to finish.

## FAQ

**How is this different from autoresearch?**
Autoresearch's core loop is universal, but the repo is wired to `train.py`, `val_bpb`, and GPU training. To use it on something else you'd rewrite the setup. This gives you that loop ready to go for any codebase.

**When would I use this instead of ML?**
It's not instead of ML. ML is one possible domain. This works on anything where the agent can try things, measure, and iterate. Code, scripts, documents, configs. Slow builds, flaky tests, API latency, prompt accuracy.

**How does it measure success for non-ML code?**
Whatever you can measure. Test pass rate, benchmark output, type check errors, build time. You set it up in the discovery phase. The agent asks what to measure and how. If you can run a command and get a number, that's your metric. For cases where there's no command to run, the agent scores against a qualitative rubric you define together. That part is less precise but the rest of the loop stays the same.

**How does convergence detection work?**
Both numerical and pattern-based. Metric plateau (<0.5% over last 5 keeps) is numerical. 5+ discards in a row, same code area modified 3+ times, alternating keep/discard on similar changes are pattern-based. The agent checks a signals table after every experiment and decides what to do. Not a hard-coded state machine, more like a checklist of "if you see this, try that."

**Can it improve itself?**
Sort of. The skill was optimized using the skill itself. A research document about how LLMs process instructions (attention decay, primacy/recency, instruction budgets) was used as criteria, and the agent ran the loop against its own prompt. Not fully recursive, but the loop was: research → skill → use skill to improve skill.

**Can't I just ask Claude to build this from the autoresearch repo?**
You can try. This saves you the work and includes things autoresearch doesn't have: thought experiments, non-linear branching, convergence detection, qualitative metrics, session resume.

## License

MIT

## See also

**[Yggdrasil](https://github.com/krzysztofdudek/Yggdrasil)** — the agent experiments on your code. But does it understand what it's working on? Semantic memory for repositories.
