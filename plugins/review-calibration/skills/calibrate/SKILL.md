---
name: calibrate
description: >-
  Turn an annoying agent behavior into ONE durable, executable calibration rule and add it
  to the right on-disk location so it holds across model releases and context resets. Use
  when Claude is too verbose, too eager, over-flags, won't stop, uses the wrong tone/format,
  or any "it keeps doing X" — or when the user says "calibrate", "/calibrate", "make a rule
  for this", or "stop doing X". For the theory and the review eval, see the plugin's
  CALIBRATION.md and RUNBOOK.md.
---

# Calibrate

Convert a behavior complaint into ONE executable rule on disk. Executable = checkable by
reading the output: a number, an if-X-then-Y, or an explicit don't. Adjectives are banned —
they re-roll on every new model and give false confidence.

## Input

`/calibrate <behavior>` — e.g. `/calibrate stop writing long preambles`.
If no behavior is given, ask one question: "What does Claude do that you want to change?"

## Procedure

1. **Classify** the behavior (guides phrasing + placement):
   verbosity | scope/over-eagerness | nitpick/over-flagging | stopping | tone | format | other.

2. **Write it as an executable rule.** Reject adjectives; make it checkable. Examples:
   | Complaint | Rule |
   |---|---|
   | too verbose | Answer in <=4 sentences unless I ask for detail or the task is multi-step. |
   | over-eager | Change only what I asked; if a fix needs more, stop and ask first. |
   | over-flags style | Report a finding only with a concrete repro; floor is correctness/security/data-loss. |
   | won't stop | Stop when the request is satisfied and checks pass; add nothing unrequested. |
   | wrong tone | (name the concrete tell, e.g.) No "Great question!"/"Sure!"/"Let me..."; start with the answer. |
   If you cannot make it checkable, say so and ask a clarifying question instead of writing a vague line.

3. **Pick the destination:**
   - Everyday Claude behavior -> `~/.claude/CLAUDE.md`, `## Calibration` section.
   - Project-specific -> that project's `CLAUDE.md`.
   - Code-review behavior -> the review skill's prompt (and note it is measurable with the
     bundled harness at `${CLAUDE_PLUGIN_ROOT}/harness`).

4. **Check for conflict / dilution.** Read the target's `## Calibration` section first.
   - If an existing line already covers it, propose TIGHTENING that line, not adding a new one.
   - If adding would push the block past ~6-8 lines, propose pruning a stale line too.

5. **Confirm, then write.** Show the exact line + file + section and get a yes before editing
   (never edit CLAUDE.md unconfirmed). Apply with Edit, preserving everything else. If the
   `## Calibration` section does not exist yet, create it.

6. **Close** with three facts:
   - It takes effect **next session** (CLAUDE.md is read at session start), not this one.
   - Durability: fully executable (transfers across models) vs semi-durable (leans against a
     default — flag which it is).
   - For review rules, offer to verify the change with the eval:
     `cd "${CLAUDE_PLUGIN_ROOT}/harness"; ./run.ps1 -Models <id> -Passes 3; ./score.ps1`.

## Rules

- One behavior -> one rule per invocation. Keep it surgical.
- Executable or nothing. An adjective on disk is worse than no rule.
- This is calibration, not memory — never store the rule as an auto-memory. It lives in
  CLAUDE.md or a skill.
- Prune as you go; a tight block transfers better than an exhaustive one.
