# Findings: calibration vs. model version

- **2026-08-19:** initial study, 12-case C# corpus.
- **2026-08-19 (re-baseline):** 20-case polyglot corpus (TS/SQL/C#). Numbers below are the
  re-baseline; it separates the models more cleanly than the 12-case run and is the current
  reference.

## Question

Team perception: each new model (Opus 4.8 -> 5) feels great briefly, then "degraded" —
nitpicky, sometimes dumb, sometimes introducing bugs while fixing caught ones — prompting
a revert. Recurs every release. Is it the model, or how we calibrate it?

## Method

Review-eval harness: 20 cases (12 buggy, 8 clean false-positive traps) across TypeScript,
SQL, and C#. Reviewer runs headless (`claude -p --model <id>`), 3 passes/model. Two prompt
modes:
- **STRICT** — mirrors the Calibration contract (repro required; correctness/security/
  data-loss floor). The reviewer as you'd deploy it.
- **LOOSE** — generic "comment on anything", no floor. The model on its own defaults.

Scored on `recall` (planted bugs caught) and `clean-FP/run` (findings on clean code = the
"nitpicky" signal). 240 reviews total, 0 parse errors, full coverage.

## Results (20-case corpus)

```
STRICT (calibrated)     recall  clean-FP/run
  claude-opus-4-8         100%          0.0
  claude-opus-5           100%          0.7*

LOOSE (no calibration)  recall  clean-FP/run
  claude-opus-4-8         100%          7.7
  claude-opus-5           100%         19.3

* 5's entire strict FP is one ambiguous case (12-clean-style-not-bug): it flagged that
  Trim()+ToLower widens accepted input, a real behavior change IF a caller relied on exact
  match. Defensible judgment, not a nitpick. Calibrated, the models are effectively tied.
```

## Conclusions

1. **Calibration dwarfs model choice — roughly an order of magnitude.** Removing the prompt
   swings FP by +7.7 (4.8) and +18.6 (5) per run. The calibrated model gap is 0.7 (and ~0
   under scrutiny). The *uncalibrated* model gap is 11.6. Calibration is worth ~10-25x the
   model version, and it specifically neutralizes 5's higher raw tendency.
2. **The complaint is real, but only uncalibrated.** Raw, 5 is ~2.5x nitpickier than 4.8
   (19.3 vs 7.7) — the bigger corpus shows this more clearly than the 12-case run (which read
   ~1.6x). Calibration removes ~96% of it; calibrated, the models are tied (0.0 vs 0.7*).
3. **Neither model is dumb.** Recall stayed 100% in BOTH modes for BOTH models, including
   the subtle bugs (floating promise, lexicographic sort, NOLOCK dirty read, `= NULL`,
   dropped `using`). 5 is *noisier*, not weaker — noise buries real findings, which reads as dumb.

## Decision

Invest in calibration, not model selection. Do NOT pin away from 5 for reviews — calibrated,
it matches 4.8. 5 simply needs calibration *more* than 4.8 did (larger loose->strict drop),
and once it has it, the difference is one debatable case. New-model playbook: run the eval,
read the STRICT column; ship if recall holds and strict-FP is near baseline.

## Caveats

- LOOSE is a deliberately extreme null-calibration prompt; real use sits between, so the
  true gap is smaller than 7.7-19.3 but larger than 0.0-0.7.
- 20 cases. Direction is strong and consistent across two corpus sizes; exact multipliers
  are still soft. Quote "~an order of magnitude", not a point number.

## Meta-lessons (the corpus author needs review too)

- **Case 09** was authored as "clean" but is actually an over-narrowed-catch regression
  (narrowing `catch(Exception)` to `catch(IOException)` lets `UnauthorizedAccessException`
  etc. escape a best-effort contract). Both models correctly flagged it; the eval caught the
  mislabel.
- **Case 12** is genuinely ambiguous — 5's strict "FP" there is a defensible call, not an
  error. Where a case is a judgment call, the number should carry a footnote, not a verdict.
- Trust neither a single feeling nor a single number.
