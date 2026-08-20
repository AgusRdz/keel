# behavior-eval

The `harness/` sibling measures calibration on the **review prompt**. This measures it on
**general agent behavior** — the scope-lock / stop-when-done / minimal-diff rules that live
in a `CLAUDE.md`. Same idea: controlled, repeated, scored — never eyeballed.

## Why it exists

Hand-probing "is Claude un-calibrated?" with one prompt is an anecdote: n=1, no control,
confounded by whatever other rules survive, and only on tasks easy enough that the model's
default already behaves. This turns it into an A/B measurement.

## Design

- **Two arms**, identical except for one variable:
  - `arms/control/CLAUDE.md` — re-adds the calibration block (calibrated)
  - `arms/treatment/CLAUDE.md` — no rules (un-calibrated)
  Each is dropped into the run's workdir as a project `CLAUDE.md`. The user's global
  `~/.claude/CLAUDE.md` loads in **both** arms, so it cancels — the block is the only
  difference.
- **Probes** (`probes/<id>/`): a narrow request (`task.txt`) over seed files (`seed/`)
  planted with out-of-scope **bait**, plus a `rubric.txt` defining what counts as an
  over-reach violation. Scope creep and unrequested extras are *counted*, not judged by feel.
- **Ground truth = the on-disk diff.** `run.py` records what the agent actually changed
  (unified diff vs seed), not its self-report. Saying "I also noticed X" without editing X
  is not a violation.
- **Repeated**: N runs per (arm, probe) — model behavior is non-deterministic.
- **Scored by an LLM judge** (`score.py`) against each probe's rubric → mean violations/run
  per arm. `treatment > control` means the block was doing work; `treatment ≈ control` means
  it was redundant on these probes.

## Run

Requires the `claude` CLI on `PATH` and Python 3.8+ (stdlib only).

```bash
cd plugins/review-calibration/behavior-eval
python run.py --runs 3          # 2 arms × 3 probes × 3 = 18 agent calls
python score.py                 # 18 judge calls → table
```

Flags: `run.py --arms treatment --probes 02-add-divide --runs 5 --model <id>`.

## Caveats

- Probes must carry real bait, and be easy enough that the *in-scope* action is unambiguous —
  otherwise you measure task difficulty, not scope discipline.
- The judge is itself a model; spot-check its `items` on a few runs before trusting the means.
- Small N + few probes → treat the direction as signal, the exact means as soft (same rule as
  the review harness).
