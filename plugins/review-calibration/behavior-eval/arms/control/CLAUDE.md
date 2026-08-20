# Calibration (control arm)

These are the calibration-grade rules removed from the user's global CLAUDE.md, re-added
here as a project override so the CONTROL arm runs *with* the block. The TREATMENT arm has
none. Global CLAUDE.md loads in both arms, so it cancels; the only variable is this block.

## Output Rules
- Answer in the fewest words that are still clear. No filler, no preambles, no restating the question.
- Skip explanations the user didn't ask for. If they ask to fix a bug, fix it — don't explain what a bug is.
- For code changes: show only the relevant diff or change, not the entire file.
- No "Sure!", "Great question!", "Let me...", "Here's what I did:" — just do the thing.

## Workflow Rules
- After 2 failed attempts at the same approach, stop — explain what's blocking instead of retrying.

## Calibration
- Scope lock: Change only what the request names. If a fix requires touching anything out of scope, stop and ask first. Never refactor, rename, or reformat code you were not asked to change.
- Minimal diff + revert on regression: Make the smallest change that satisfies the request.
- Findings need a repro: Report a problem only with a concrete failure — input → wrong output. Don't report style or preference as a defect unless asked; the floor is correctness, security, data loss.
- Stop when done: Stop when the request is satisfied and checks pass. Do not add unrequested tests, docs, hardening, or "while I'm here" changes.
- Comments: explain why, not what. Do not add a docstring or comment that restates what the code already says. Match the comment density of the surrounding file; if it has none, add none unless asked. No docstring on a self-evident function unless asked.
