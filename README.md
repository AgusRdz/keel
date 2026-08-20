# Review Calibration

A Claude Code plugin for one recurring problem: **a new model ships, your reviews (or your
agent) suddenly feel nitpicky / dumb / degraded, so the team reverts.** This plugin says
don't chase the model — *calibrate* it, then *measure*.

Measured result across 240 reviews: **calibration outweighs model choice by roughly an
order of magnitude.** Calibrated, Opus 4.8 and Opus 5 are effectively tied; uncalibrated,
5 is ~2.5× noisier. Full study in [`docs/FINDINGS.md`](plugins/review-calibration/docs/FINDINGS.md).

```
STRICT (calibrated)     recall  clean-FP/run     20-case corpus, TS/SQL/C#
  claude-opus-4-8         100%          0.0
  claude-opus-5           100%          0.7*
LOOSE (no calibration)  recall  clean-FP/run
  claude-opus-4-8         100%          7.7
  claude-opus-5           100%         19.3
```
<sub>* 5's only strict FP is one genuinely ambiguous case; calibrated, the models are tied. Recall never drops — models get *noisier*, not weaker, which reads as "dumb".</sub>

## Install

```
/plugin marketplace add AgusRdz/review-calibration-eval
/plugin install review-calibration@review-calibration-eval
```

Then reload if needed (`/reload-plugins`). Two skills become available:

| Skill | What it does |
|---|---|
| `/review-calibration:calibrate <behavior>` | Turn an annoying behavior ("too verbose", "keeps refactoring", "flags style") into ONE executable, on-disk rule and add it to your `CLAUDE.md`. |
| `/review-calibration:review-eval` | Run / interpret the model-vs-model regression eval, and follow the per-release ship-vs-tune runbook. |

## The idea in three parts

1. **Calibration block** — write the reviewer's/agent's behavior as *executable* rules
   (a number, an if-X-then-Y, or an explicit don't — never an adjective) and keep them
   **on disk** (`CLAUDE.md` / a skill). Executable rules transfer across model versions;
   on-disk rules survive `/clear` and context compaction. See
   [`CALIBRATION.md`](plugins/review-calibration/CALIBRATION.md).
2. **Eval harness** — a regression test for the *reviewer*, not the code. Feed it diffs with
   known ground truth; it scores any model on recall (bugs caught) vs. false-positive rate
   (the "nitpicky" number). Turns "5 feels degraded" into a number.
3. **Runbook** — on each model release, run the eval, read the STRICT column, ship if recall
   holds and FP is near baseline; tune one rule if it drifted. See
   [`RUNBOOK.md`](plugins/review-calibration/RUNBOOK.md).

## Running the eval

Requires the `claude` CLI on `PATH` and PowerShell 7+ (`pwsh`). No Python needed
(a `score.py` mirror is included for anyone who has real Python).

```powershell
cd "${CLAUDE_PLUGIN_ROOT}/harness"      # or the plugin's install dir
./run.ps1 -Models claude-opus-4-8,claude-opus-5 -Passes 3   # strict = calibrated prompt
./run.ps1 -Models claude-opus-4-8,claude-opus-5 -Passes 3 -PromptMode loose
./score.ps1 -Mode both                  # strict vs loose, side by side
```

Deterministic scorer self-test (no model calls): `pwsh ./tests/test-score.ps1`.

## Repo layout

```
.claude-plugin/marketplace.json         # marketplace (lists the plugin)
plugins/review-calibration/
  .claude-plugin/plugin.json            # plugin manifest
  skills/calibrate/SKILL.md             # /review-calibration:calibrate
  skills/review-eval/SKILL.md           # /review-calibration:review-eval
  CALIBRATION.md  RUNBOOK.md            # method + per-release loop
  harness/  tests/  docs/               # eval, self-test, findings
```

## Honest limits

- The eval measures the reviewer **on its corpus** (20 cases). Grow `harness/cases/` toward
  the bugs *you* care about — the corpus IS the eval.
- Line-window matching (±3) is coarse — catches a 40% FP gap, not a 2%.
- `LOOSE` is a deliberately extreme null-calibration prompt; real use sits between the two
  columns. Quote "~an order of magnitude", not a point number.

## License

MIT — see [`LICENSE`](LICENSE).
