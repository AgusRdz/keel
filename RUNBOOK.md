# Runbook: calibrating across model releases

Two events, don't conflate them:
- **Release = when you RUN the check.** Cheap, every release.
- **Drift = when you EDIT the block.** Rare; only when the number moves.

You do NOT re-calibrate from scratch each release. The block is authored once and is
durable. Per release you verify, and tune only the one line that drifted, if any.

---

## Per-release loop (~20 min)

Triggered by a new model shipping.

1. **Run the eval, STRICT, on the new model.**
   ```powershell
   cd harness
   ./run.ps1 -Models <new-model-id> -Passes 3
   ./score.ps1
   ```

2. **Read two numbers in the STRICT table:**
   - `recall` — did it still catch the planted bugs?
   - `clean-FP/run` — findings raised on clean code (the "nitpicky" number).

3. **Decision:**

   | Observation | Action |
   |---|---|
   | recall held AND clean-FP near baseline | **Ship. No edit.** (common case) |
   | clean-FP crept up | **Tune one line** (step 4) |
   | recall dropped | Investigate the missed case before shipping; the model may be weaker on that bug class, or the case regressed |
   | a case looks mis-scored | Check the corpus — you may have mislabeled it (see case 09) |

4. **Tune (only if drift):**
   - Find *which* clean case gained findings (per-case dump below).
   - That maps to the behavior the model now over-does -> tighten the one governing line in
     the Calibration block with a number/condition (see `CALIBRATION.md`).
   - Re-run step 1. Loop until clean-FP is back to baseline.
   - Commit the block change with a note: which model, which line, why.

Per-case dump (which clean case is noisy):
```powershell
# after a run, list findings-per-pass on each clean case for a model
$m = 'claude-opus-5'
Get-ChildItem harness/cases -Directory | Where-Object Name -like '*clean*' | ForEach-Object {
  $c = $_.Name
  $counts = 1..3 | ForEach-Object {
    $f = "harness/results/strict/$m/pass$_/$c.json"
    if (Test-Path $f) { @((Get-Content $f -Raw | ConvertFrom-Json).findings).Count } else { '-' }
  }
  "{0,-34} {1}" -f $c, ($counts -join ', ')
}
```

---

## Diagnosing calibration-sensitivity (optional, when you want the "why")

Run both the old and new model under the LOOSE prompt (calibration removed) and compare:
```powershell
cd harness
./run.ps1 -Models <old-id>,<new-id> -Passes 3 -PromptMode loose
./score.ps1 -Mode both
```
- **Large loose clean-FP + near-zero strict clean-FP** = "fine once calibrated." Don't avoid
  the model; give it the block.
- **strict->loose delta bigger for the new model** = it needs tighter calibration than the
  old one. Add/tighten a line, don't revert.

---

## Continuous (not tied to releases)

- You correct the same new behavior 3+ times in daily use -> add one executable line to the block.
- Block grows past ~6-8 lines -> prune lines the model now handles by default.
- A model exposes a corpus gap (finds a real bug you didn't label, or a "clean" case is
  actually buggy) -> fix `cases/`, re-run. The corpus is the eval; keep it honest.

---

## Baselines (2026-08-19, 20-case corpus: 12 buggy, 8 clean; TS/SQL/C#)

| Mode | Model | recall | clean-FP/run |
|---|---|---|---|
| STRICT | claude-opus-4-8 | 100% | 0.0 |
| STRICT | claude-opus-5 | 100% | 0.7* |
| LOOSE | claude-opus-4-8 | 100% | 7.7 |
| LOOSE | claude-opus-5 | 100% | 19.3 |

\* 5's entire strict FP is one ambiguous case (`12-clean-style-not-bug`), where flagging
input-widening is a defensible judgment call, not sloppiness. Calibrated, the models are
effectively tied.

Read: calibrated, both models are near-perfect (0.0 / 0.7). Uncalibrated, 5 is ~2.5x
noisier than 4.8 (19.3 vs 7.7). Calibration removes ~100% of 4.8's nitpicking and ~96% of
5's — and specifically neutralizes 5's higher raw tendency. Recall stays 100% everywhere.

Re-baseline when you materially grow the corpus. n=20 separates the models more cleanly
than the earlier n=12 run; still treat exact multipliers as "~an order of magnitude".
