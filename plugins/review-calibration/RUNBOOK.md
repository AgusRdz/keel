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

## Baselines (2026-08-20, 32-case corpus: 18 buggy, 14 clean; TS/SQL/C#/Python/Go)

| Mode | Model | recall | clean-FP/run |
|---|---|---|---|
| STRICT | claude-opus-4-8 | 100% | 0.0 |
| STRICT | claude-opus-5 | 100% | 0.0 |
| LOOSE | claude-opus-4-8 | 100% | 3.3 |
| LOOSE | claude-opus-5 | 100% | 4.7 |

Read: calibrated, both models sit at a flat 0.0 FP — 5's one debatable strict-FP from the
20-case run (`12-clean-style-not-bug`) is gone at this scale. Uncalibrated, 5 stays the
noisier model (4.7 vs 3.3), same ordering as every prior run. Recall stays 100% everywhere.

Loose magnitude fell vs the 20-case run (was 7.7 / 19.3): the added clean cases are easy
equivalences (f-string, template literal, destructure-rename) that even LOOSE rarely flags,
gentling the denominator. Durable result = sign and ordering (loose ≫ strict, 5 > 4.8), not
the point number; treat multipliers as corpus-sensitive.

Re-baseline when you materially grow the corpus. Prior baselines: n=20 (2026-08-19, TS/SQL/C#),
n=12 (2026-08-19, C# only) — see `docs/FINDINGS.md` for the full history.
