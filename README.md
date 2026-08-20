# review-calibration-eval

Keep code-review quality stable across model releases by **calibrating the reviewer
instead of chasing or avoiding model versions.**

New model ships -> review feels nitpicky/dumb -> team reverts. This repo says: don't
chase the model. Write the reviewer's behavior down as executable, on-disk rules, then
measure each release with a regression eval. Measured result: **calibration outweighs
model choice by roughly an order of magnitude** (`docs/FINDINGS.md`).

```
STRICT (calibrated)     recall  clean-FP/run     (20-case corpus, TS/SQL/C#)
  claude-opus-4-8         100%          0.0
  claude-opus-5           100%          0.7*
LOOSE (no calibration)  recall  clean-FP/run
  claude-opus-4-8         100%          7.7
  claude-opus-5           100%         19.3
```
\* 5's only strict FP is one ambiguous case; calibrated, the models are effectively tied.

## Contents

| Path | What |
|---|---|
| `SKILL.md` | Claude Code skill entry (name, when-to-use, how-to-use) |
| `CALIBRATION.md` | The Calibration block + how to write executable, durable lines |
| `RUNBOOK.md` | Per-release verify/tune loop and the ship-vs-tune decision rule |
| `harness/` | The eval: `reviewer.ps1`, `run.ps1`, `score.ps1` (+ `score.py`), `cases/`, `lib/` |
| `tests/` | Deterministic scorer self-test (no model calls) |
| `docs/FINDINGS.md` | The 2026-08-19 study behind the ~20x result |

## Quick start

Requires the `claude` CLI on PATH and PowerShell 7+ (`pwsh`). No Python needed (a `score.py`
mirror is included for anyone who has real Python; this machine's `python` is a Store stub).

```powershell
# 1. run the eval on one or more models (strict = calibrated prompt)
cd harness
./run.ps1 -Models claude-opus-4-8,claude-opus-5 -Passes 3

# 2. score it
./score.ps1                 # strict table
./score.ps1 -Mode both      # strict vs loose, side by side (needs a loose run too)

# 3. run the scorer self-test (deterministic, no model calls)
cd ..
pwsh ./tests/test-score.ps1
```

## How it works

`run.ps1` feeds each `cases/<name>/{before,after}.<ext>` diff to a model via `claude -p`
and saves normalized JSON findings under `harness/results/<mode>/<model>/pass<N>/`.
`score.ps1` matches findings against `cases/<name>/truth.json` (bug at file+line, or
`clean:true`) and prints recall + false-positive rate per model. Reviews are
non-deterministic, so run multiple passes and read rates, not single shots.

Two prompt modes (`-PromptMode strict|loose`):
- **strict** mirrors the Calibration contract (repro required, correctness/security/
  data-loss floor) — the reviewer as you'd deploy it.
- **loose** is a generic "comment on anything" prompt — the model on its defaults, to
  measure how much calibration it needs.

## Honest limits

- Line-window matching (±3) is coarse — catches a 40% FP gap, not a 2% one.
- Measures the reviewer ON THIS CORPUS (12 cases). Grow `cases/` toward the bugs you care
  about; the corpus IS the eval.
- `buggy-unmatched` can be a real bug you forgot to label, not a false positive — eyeball it.

## Status

Local repo. Not yet pushed to a remote.
