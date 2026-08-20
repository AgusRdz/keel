# Findings: calibration vs. model version (2026-08-19)

## Question

Team perception: each new model (Opus 4.8 -> 5) feels great briefly, then "degraded" —
nitpicky, sometimes dumb, sometimes introducing bugs while fixing caught ones — prompting
a revert. Recurs every release. Is it the model, or how we calibrate it?

## Method

Review-eval harness: 12 cases (7 buggy, 5 clean false-positive traps). Reviewer runs
headless (`claude -p --model <id>`), 3 passes/model. Two prompt modes:
- **STRICT** — mirrors the Calibration contract (repro required; correctness/security/
  data-loss floor). The reviewer as you'd deploy it.
- **LOOSE** — generic "comment on anything", no floor. The model on its own defaults.

Scored on `recall` (planted bugs caught) and `clean-FP/run` (findings on clean code = the
"nitpicky" signal).

## Results

```
STRICT (calibrated)     recall  clean-FP/run
  claude-opus-4-8         100%          0.3
  claude-opus-5           100%          0.7

LOOSE (no calibration)  recall  clean-FP/run
  claude-opus-4-8         100%          8.3   (~28x vs its strict)
  claude-opus-5           100%         13.0   (~19x vs its strict)
```

## Conclusions

1. **Calibration ~20x the model effect.** Removing the prompt swings FP by +8.0 (4.8) and
   +12.3 (5) per run. The entire 4.8-vs-5 gap under calibration is +0.4.
2. **The complaint is real but small, and only surfaces uncalibrated.** Raw, 5 is ~57%
   nitpickier (13.0 vs 8.3). Calibration crushes ~95% of it; residual gap (0.7 vs 0.3) is trivial.
3. **Neither model is dumb.** Recall stayed 100% in BOTH modes for BOTH models, including
   the subtle bugs. 5 is *noisier*, not weaker — noise buries real findings, which reads as dumb.

Nuance: 5 isn't uniformly worse. Loose, it hammered method-extraction (case 07) and a
ToLower case (12) but stayed silent on a guard-clause refactor (08) where 4.8 nitpicked.
They nitpick *different* things.

## Decision

Invest in calibration, not model selection. Do NOT pin away from 5 for reviews. The
Calibration block (executable lines, on disk) is the fix, and it earns ~20x what model
choice does. New-model playbook: run the eval, read the STRICT column; ship if recall
holds and strict-FP is near baseline.

## Caveats

- LOOSE is a deliberately extreme null-calibration prompt; real use sits between, so the
  true gap is smaller than 8-13 but larger than 0.3-0.7.
- 12 cases only. Direction is strong and consistent; exact multipliers are soft. Quote
  "~an order of magnitude", not "20x" as gospel.

## Meta-lesson

The eval caught a mislabeled case: 09 was authored as "clean" but is actually an
over-narrowed-catch regression (narrowing `catch(Exception)` to `catch(IOException)` lets
`UnauthorizedAccessException` etc. escape the best-effort contract). Both models correctly
flagged it. Trust neither a single feeling nor a single number — the corpus author needs
adversarial review too.
