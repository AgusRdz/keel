# Scores review-eval results against ground truth. Pure PowerShell (no Python needed).
# Usage: ./score.ps1 [-Mode strict|loose|both] [-Window 3]
[CmdletBinding()]
param(
    [ValidateSet('strict', 'loose', 'both')][string]$Mode = 'strict',
    [int]$Window = 3
)
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
. (Join-Path $root 'lib/scoring.ps1')

$truth = Get-Truth -CasesDir (Join-Path $root 'cases')
$nClean = @($truth.Values | Where-Object { $_.clean }).Count
$nBuggy = $truth.Count - $nClean
$modes = if ($Mode -eq 'both') { @('strict', 'loose') } else { @($Mode) }

Write-Host ""
Write-Host ("review-eval  |  cases: {0} ({1} buggy, {2} clean)  |  window: +/-{3} lines" -f $truth.Count, $nBuggy, $nClean, $Window)

$fmt = "{0,-24} {1,6} {2,8} {3,13} {4,14} {5,16}"
foreach ($mode in $modes) {
    $rows = Get-ModelScores -Truth $truth -ResultsModeDir (Join-Path $root "results/$mode") -Window $Window
    Write-Host ""
    Write-Host ("=== PROMPT MODE: {0} ===" -f $mode.ToUpper())
    if ($rows.Count -eq 0) { Write-Host "  (no results -- run: ./run.ps1 -PromptMode $mode)"; continue }
    Write-Host ($fmt -f 'model', 'passes', 'recall', 'clean-FP/run', 'nitpick/clean', 'buggy-unmatched')
    Write-Host ('-' * 86)
    foreach ($r in $rows) {
        $nitpick = if ($nClean) { $r.clean_fp / $nClean } else { 0 }
        Write-Host ($fmt -f $r.model, $r.passes, ("{0:P0}" -f $r.recall), ("{0:N1}" -f $r.clean_fp), ("{0:N2}" -f $nitpick), ("{0:N1}" -f $r.buggy_unmatched))
    }
}
Write-Host ""
Write-Host "Higher recall = better.  Lower clean-FP/run = better (the 'nitpicky' number)."
Write-Host "strict->loose delta = how much each model nitpicks WITHOUT the Calibration prompt."
