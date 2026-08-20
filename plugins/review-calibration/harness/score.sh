#!/usr/bin/env bash
# Cross-platform dispatcher for the review-calibration scorer.
#
# Canonical CLI: --mode strict|loose|both   --window <n>
#
# Runtime selection: pwsh on PATH -> score.ps1 (-Mode/-Window); else python3/python
# -> score.py (--mode/--window, same names, forwarded as-is); else exit 1 naming
# both install options. See run.sh for the fuller rationale on the pwsh translation.
set -eo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MODE=""
WINDOW=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="$2"; shift 2 ;;
    --window)
      WINDOW="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: score.sh [--mode strict|loose|both] [--window N]"
      exit 0
      ;;
    *)
      echo "score.sh: unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

ps_quote() {
  local s="${1//\'/\'\'}"
  printf "'%s'" "$s"
}

# On Git Bash/MSYS, pwsh needs a Windows path, not an MSYS /c/... path.
to_win() {
  if command -v cygpath >/dev/null 2>&1; then cygpath -w "$1"; else printf "%s" "$1"; fi
}

if command -v pwsh >/dev/null 2>&1; then
  CMD="& $(ps_quote "$(to_win "$DIR/score.ps1")")"
  [[ -n "$MODE" ]] && CMD+=" -Mode $(ps_quote "$MODE")"
  [[ -n "$WINDOW" ]] && CMD+=" -Window $(ps_quote "$WINDOW")"
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
  [[ -n "$MODE" ]] && PYARGS+=(--mode "$MODE")
  [[ -n "$WINDOW" ]] && PYARGS+=(--window "$WINDOW")
  exec "$PY" "$DIR/score.py" "${PYARGS[@]}"
fi

echo "score.sh: no runtime found. Install one of:" >&2
echo "  - PowerShell 7+ (pwsh): https://aka.ms/powershell" >&2
echo "  - Python 3.8+: https://www.python.org/downloads/" >&2
exit 1
