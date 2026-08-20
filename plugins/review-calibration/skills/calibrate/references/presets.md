# Calibration preset catalog

Curated, vetted, executable calibration rules. Each is checkable by reading the output
(a number, an if-X-then-Y, or an explicit don't) — no adjectives. Menu mode presents these
for selection and writes the chosen ones into the target's `## Calibration` section.

Keep the applied block tight (~6–8 lines). If a selection would exceed that, warn and offer
to prune. Dedupe against rules already present — if one is covered, tighten it, don't dup.

| key | category | destination | rule (write verbatim) |
|---|---|---|---|
| `verbosity-brief` | verbosity/tone/format | `~/.claude/CLAUDE.md` | Lead with the answer. Fewest words that stay clear; no preamble, filler, or restating the question. Plain words over jargon; explain only what was asked. |
| `comments-why-not-what` | code quality | `~/.claude/CLAUDE.md` | Comments explain why, not what. Match the file's existing comment density — none means none — unless asked. No docstring on a self-evident function. |
| `scope-lock` | scope/over-eagerness | `~/.claude/CLAUDE.md` | Change only what the request names. If a fix needs out-of-scope edits, stop and ask first. |
| `production-floor` | code quality | `~/.claude/CLAUDE.md` | Code must run and handle the inputs the task implies; match the surrounding file's structure and error-handling level; leave no TODO/stub/placeholder or dead code. Do NOT add logging, config, validation, or abstraction the task didn't ask for. |
| `stop-when-done` | stopping | `~/.claude/CLAUDE.md` | Stop when the request is satisfied and checks pass; add nothing unrequested. After 2 failed attempts at one approach, stop and report what's blocking. |
| `no-over-flagging` | nitpick/over-flagging | review skill prompt (or `~/.claude/CLAUDE.md`) | Report a finding only with a concrete repro (input → wrong output); floor is correctness/security/data-loss. No style/preference unless asked. |

## Notes for the applying agent

- `production-floor` intentionally ends with an explicit *don't* — "production" without it becomes
  a license to gold-plate, which fights `scope-lock`/`stop-when-done`. Keep the clause.
- `no-over-flagging` is review-time behavior. If the user does code review via a skill, prefer
  writing it into that skill's prompt (it is measurable with the harness); otherwise `CLAUDE.md`.
- On today's Opus, `scope-lock` and `stop-when-done` are largely redundant with the model's
  default (see behavior-eval); `comments-why-not-what` and `verbosity-brief` are the two that
  most change behavior interactively. Mention this if the user asks "which actually matter".
