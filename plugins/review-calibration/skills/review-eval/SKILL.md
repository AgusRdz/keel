---
name: review-eval
description: >-
  Keep code-review (and general agent) quality stable across model releases by
  calibrating the reviewer instead of chasing or avoiding model versions. Use when
  a new model ships and someone says it "got nitpicky / dumb / degraded", when
  deciding whether to upgrade the review model, or when review output feels noisy.
  Provides an executable Calibration block, a per-release runbook, and a regression
  eval harness that scores any model on recall vs. false-positive rate.
---

# Review Calibration

## What this is

A method and a harness for one problem: **new model ships, review quality feels
worse, team reverts.** This skill says don't chase the model — calibrate the
reviewer, then measure. Empirically, calibration outweighs model choice by roughly
an order of magnitude (see `docs/FINDINGS.md`).

Core claims, all measured (32-case corpus, TS/SQL/C#/Python/Go, `docs/FINDINGS.md`):
- Calibration moves false positives far more than the model version does — removing the
  prompt swings FP by several points/run; calibrated, the model gap collapses to ~0.
- "Nitpicky new model" is real (5 stays noisier than 4.8 uncalibrated, every corpus) but
  calibration removes essentially all of it — calibrated, both models sit at 0.0 FP.
- Models rarely lose recall across versions — they get *noisier*, which reads as dumb.
- Exact multipliers are corpus-sensitive; the durable result is the sign and ordering
  (loose ≫ strict, 5 > 4.8), not a point number.

## When to use

- A new model released and review output feels degraded / nitpicky / trigger-happy.
- Deciding whether to switch the review model.
- Authoring or tightening the Calibration block.
- Any time you want a *number* for "is this model better for reviews" instead of a vibe.

## How to use

### 1. Calibrate (author once, tune rarely)
Read `${CLAUDE_PLUGIN_ROOT}/CALIBRATION.md`. Copy the Calibration block into the consumer's on-disk
instructions (`CLAUDE.md`, a rule file, or a review skill) — NOT into chat, which
compaction and `/clear` erase. Write every line executable (number / condition /
stop-rule), never an adjective.

### 2. Verify on each release (the runbook)
Follow `${CLAUDE_PLUGIN_ROOT}/RUNBOOK.md`. In short:
```powershell
cd "${CLAUDE_PLUGIN_ROOT}/harness"
./run.ps1 -Models <new-model-id> -Passes 3      # strict prompt (calibrated)
./score.ps1
```
Read the STRICT table. Recall held + clean-FP near baseline => ship, no edit.
FP crept up => find the drifted clean case, tighten the one governing line, re-run.

### 3. Diagnose calibration-sensitivity (optional)
```powershell
./run.ps1 -Models <a>,<b> -Passes 3 -PromptMode loose
./score.ps1 -Mode both
```
The strict->loose delta shows how much a model nitpicks WITHOUT calibration — i.e.
how much calibration it needs. Big loose FP + near-zero strict FP = "fine once calibrated."

## Layout (all under the plugin root, `${CLAUDE_PLUGIN_ROOT}`)

- `CALIBRATION.md` — the block + how to write executable, durable lines.
- `RUNBOOK.md` — the per-release verify/tune loop and the ship-vs-tune decision rule.
- `harness/` — the eval: `reviewer.ps1`, dual dispatchers `run.ps1`/`run.py` and
  `score.ps1`/`score.py` (+ `run.sh`/`score.sh` auto-detect), `cases/` (by language), `lib/`.
- `docs/FINDINGS.md` — the study behind the calibration-outweighs-model result.

## Guardrails

- Keep the Calibration block small (~6-8 lines). A bloated block dilutes and drifts worse.
- The eval measures the reviewer ON THIS CORPUS. Grow `cases/` toward bugs you actually
  care about; the corpus IS the eval.
- Trust neither a single feeling nor a single number. The corpus author needs adversarial
  review too — case 09 was mislabeled and both models correctly caught it.
