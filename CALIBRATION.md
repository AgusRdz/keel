# Calibration

## The idea

An agent's output has two layers:

1. **Task content** — *what* to do. Transfers across models fine.
2. **Behavioral calibration** — *how*: thoroughness, stopping point, edit scope, what's
   worth flagging, verbosity. This is what re-rolls every model release.

When a prompt "works," you've co-adapted it to one model's defaults. That's an overfit,
and overfits don't transfer — so the next model breaks it and you re-tweak. The fix is to
**make the calibration explicit and put it on disk**, so N+1 obeys it instead of guessing.

Durability has two axes, and both are on you:
- **Across models:** write each line executable (number/condition/stop-rule), not an adjective.
  "Be concise" re-rolls; "<=6 sentences unless asked" does not.
- **Across context resets:** put it on disk (`CLAUDE.md`/rule/skill), not in chat. Chat-
  negotiated calibration dies on `/clear` and degrades on compaction (summarizers treat
  behavioral directives as chatter and drop them).

## The block

Drop these into the consumer's on-disk instructions. Every line is checkable, so it
transfers across model versions. Adjust wording to your stack; keep the executable shape.

```markdown
## Calibration

- **Scope lock:** Change only what the request names. If a fix requires touching anything
  out of scope, stop and ask first. Never refactor, rename, or reformat code you were not
  asked to change.
- **Minimal diff + revert on regression:** Make the smallest change that satisfies the
  request. After an edit, if a check or test that passed before now fails, revert that edit
  and report it - do not stack a second fix on a broken first one.
- **Findings need a repro:** Report a problem only with a concrete failure - input -> wrong
  output. No repro, don't raise it. Don't report style or preference as a defect unless
  asked; the floor is correctness, security, data loss.
- **Stop when done:** Stop when the request is satisfied and checks pass. Do not add
  unrequested tests, docs, hardening, or "while I'm here" changes.
```

Each line maps to a failure mode: scope lock -> over-eagerness/unrequested refactors;
minimal-diff+revert -> fixes that introduce bugs / review spirals; findings-need-a-repro ->
nitpicking / non-convergent review; stop-when-done -> scope creep.

## Durable vs. fragile (know which you're writing)

- **Fully executable (transfers cleanly):** scope lock, revert-on-regression,
  findings-need-a-repro, stop-when-done. Conditions and explicit don'ts.
- **Semi-durable (leans against a default, biases but doesn't guarantee):** "smallest
  change / minimal diff." Carried by the hard revert rule beside it. If it drifts on a new
  model, replace the adjective with a number (e.g. "if a fix exceeds ~20 lines, stop and
  confirm scope").
- **Not durable:** anything left as an adjective ("be thorough", "use good judgment"). Those
  ARE the thing that re-rolls. Don't ship them.

## Writing new lines

1. Harvest the corrections you give repeatedly (said it 3+ times -> it's a line).
2. Phrase as `if X then Y`, a count, or an explicit don't.
3. De-dup against what's already on disk; prune lines the model now handles by default.
4. Keep the block ~6-8 lines. Fewer, sharper transfers better than exhaustive — a long
   list dilutes, and dilutes differently per model version.
