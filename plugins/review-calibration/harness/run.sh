#!/usr/bin/env bash
# Cross-platform dispatcher for the review-calibration eval runner.
#
# Canonical CLI (GNU/argparse style -- same names run.py's argparse defines):
#   --models <id>[,<id>...]   (repeatable and/or comma-separated)
#   --passes <n>
#   --prompt-mode strict|loose
#   --case-pattern <glob>      (repeatable)
#   --contract <path>
#
# Runtime selection:
#   1. pwsh on PATH  -> delegate to run.ps1. Flags are translated to run.ps1's
#      -Models/-Passes/-PromptMode/-CasePattern/-Contract param names. Multi-value
#      flags are rendered as PowerShell array literals (@('a','b')) inside a
#      `-Command` invocation -- NOT passed positionally via `-File` -- because
#      `pwsh -File run.ps1 -Models a,b` binds "a,b" as a single one-element
#      string[] (no comma-splitting) whereas `-Models @('a','b')` is unambiguous.
#   2. Otherwise python3 (or python) on PATH -> delegate to run.py, forwarding the
#      flags as-is (run.py's argparse already speaks this exact interface).
#   3. Neither found -> exit 1 naming both install options.
set -eo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MODELS=()
PASSES=""
PROMPT_MODE=""
CASE_PATTERNS=()
CONTRACT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --models)
      [[ $# -ge 2 ]] || { echo "run.sh: --models requires a value" >&2; exit 2; }
      IFS=',' read -ra parts <<< "$2"
      MODELS+=("${parts[@]}")
      shift 2
      ;;
    --passes)
      PASSES="$2"; shift 2 ;;
    --prompt-mode)
      PROMPT_MODE="$2"; shift 2 ;;
    --case-pattern)
      CASE_PATTERNS+=("$2"); shift 2 ;;
    --contract)
      CONTRACT="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: run.sh [--models id[,id...]] [--passes N] [--prompt-mode strict|loose] [--case-pattern glob] [--contract path]"
      exit 0
      ;;
    *)
      echo "run.sh: unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

# Wrap a value as a single-quoted PowerShell string literal (doubles embedded ').
ps_quote() {
  local s="${1//\'/\'\'}"
  printf "'%s'" "$s"
}

# Build a PowerShell array literal @('a','b',...) from argv.
ps_array() {
  local out="@("
  local first=1
  for v in "$@"; do
    if [[ $first -eq 0 ]]; then out+=","; fi
    out+="$(ps_quote "$v")"
    first=0
  done
  out+=")"
  printf "%s" "$out"
}

# On Git Bash/MSYS, pwsh needs a Windows path, not an MSYS /c/... path.
to_win() {
  if command -v cygpath >/dev/null 2>&1; then cygpath -w "$1"; else printf "%s" "$1"; fi
}

if command -v pwsh >/dev/null 2>&1; then
  CMD="& $(ps_quote "$(to_win "$DIR/run.ps1")")"
  if [[ ${#MODELS[@]} -gt 0 ]]; then
    CMD+=" -Models $(ps_array "${MODELS[@]}")"
  fi
  if [[ -n "$PASSES" ]]; then
    CMD+=" -Passes $(ps_quote "$PASSES")"
  fi
  if [[ -n "$PROMPT_MODE" ]]; then
    CMD+=" -PromptMode $(ps_quote "$PROMPT_MODE")"
  fi
  if [[ ${#CASE_PATTERNS[@]} -gt 0 ]]; then
    CMD+=" -CasePattern $(ps_array "${CASE_PATTERNS[@]}")"
  fi
  if [[ -n "$CONTRACT" ]]; then
    CMD+=" -Contract $(ps_quote "$(to_win "$CONTRACT")")"
  fi
  exec pwsh -NoProfile -Command "$CMD"
fi

PY=""
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
fi

if [[ -n "$PY" ]]; then
  PYARGS=()
  for m in "${MODELS[@]}"; do PYARGS+=(--models "$m"); done
  if [[ -n "$PASSES" ]]; then PYARGS+=(--passes "$PASSES"); fi
  if [[ -n "$PROMPT_MODE" ]]; then PYARGS+=(--prompt-mode "$PROMPT_MODE"); fi
  for p in "${CASE_PATTERNS[@]}"; do PYARGS+=(--case-pattern "$p"); done
  if [[ -n "$CONTRACT" ]]; then PYARGS+=(--contract "$CONTRACT"); fi
  exec "$PY" "$DIR/run.py" "${PYARGS[@]}"
fi

echo "run.sh: no runtime found. Install one of:" >&2
echo "  - PowerShell 7+ (pwsh): https://aka.ms/powershell" >&2
echo "  - Python 3.8+: https://www.python.org/downloads/" >&2
exit 1
