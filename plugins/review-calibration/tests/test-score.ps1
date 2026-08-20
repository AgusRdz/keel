# Deterministic self-test for the scoring library. NO model calls, NO network.
# Builds synthetic truth + finding files in a temp dir and asserts the scorer's math.
# Run: pwsh ./tests/test-score.ps1   (exit 0 = pass, 1 = fail)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
. (Join-Path $root 'harness/lib/scoring.ps1')

$fail = 0
function Assert-Eq($actual, $expected, $label) {
    $ok = [math]::Abs([double]$actual - [double]$expected) -lt 1e-9
    if ($ok) { Write-Host ("  PASS  {0}  (= {1})" -f $label, $actual) }
    else { Write-Host ("  FAIL  {0}  expected {1}, got {2}" -f $label, $expected, $actual); $script:fail++ }
}

# Synthetic ground truth: one buggy case (bug at line 10), one clean case.
$truth = [ordered]@{
    'a-bug'   = [pscustomobject]@{ clean = $false; bugs = @([pscustomobject]@{ file = 'after.cs'; line = 10 }) }
    'b-clean' = [pscustomobject]@{ clean = $true; bugs = @() }
}

$tmp = Join-Path ([System.IO.Path]::GetTempPath()) 'review-eval-selftest'
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }

function Write-Findings($dir, $case, $lines) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $findings = @($lines | ForEach-Object { @{ line = $_; type = 't'; severity = 'correctness'; repro = 'r' } })
    @{ findings = $findings } | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $dir "$case.json") -Encoding utf8
}

# --- Scenario 1: bug caught (finding at 11, within +/-3 of 10); clean case has 1 FP ---
$p1 = Join-Path $tmp 'pass1'
Write-Findings $p1 'a-bug'   @(11)
Write-Findings $p1 'b-clean' @(2)
$s1 = Get-PassScore -Truth $truth -PassDir $p1 -Window 3
Write-Host "Scenario 1: bug caught within window, one clean FP"
Assert-Eq $s1.recall 1.0 'recall'
Assert-Eq $s1.clean_fp 1 'clean_fp'
Assert-Eq $s1.buggy_unmatched 0 'buggy_unmatched'

# --- Scenario 2: bug MISSED (finding at 20, outside window); clean case silent ---
$p2 = Join-Path $tmp 'pass2'
Write-Findings $p2 'a-bug'   @(20)
Write-Findings $p2 'b-clean' @()
$s2 = Get-PassScore -Truth $truth -PassDir $p2 -Window 3
Write-Host "Scenario 2: bug missed (out of window), clean silent"
Assert-Eq $s2.recall 0.0 'recall'
Assert-Eq $s2.clean_fp 0 'clean_fp'
Assert-Eq $s2.buggy_unmatched 1 'buggy_unmatched'

# --- Scenario 3: window boundary is inclusive (finding at 13, exactly +3 of 10) ---
$p3 = Join-Path $tmp 'pass3'
Write-Findings $p3 'a-bug'   @(13)
Write-Findings $p3 'b-clean' @()
$s3 = Get-PassScore -Truth $truth -PassDir $p3 -Window 3
Write-Host "Scenario 3: finding exactly at window edge counts as caught"
Assert-Eq $s3.recall 1.0 'recall (edge inclusive)'

# --- Scenario 4: multi-model aggregation averages across passes ---
$mdir = Join-Path $tmp 'model-x'
Write-Findings (Join-Path $mdir 'pass1') 'a-bug' @(10)   # caught -> recall 1.0
Write-Findings (Join-Path $mdir 'pass1') 'b-clean' @(1)  # 1 FP
Write-Findings (Join-Path $mdir 'pass2') 'a-bug' @(99)   # missed -> recall 0.0
Write-Findings (Join-Path $mdir 'pass2') 'b-clean' @()   # 0 FP
$rows = Get-ModelScores -Truth $truth -ResultsModeDir $tmp -Window 3
$row = $rows | Where-Object { $_.model -eq 'model-x' }
Write-Host "Scenario 4: aggregation averages recall (1.0,0.0)->0.5 and clean_fp (1,0)->0.5"
Assert-Eq $row.passes 2 'passes'
Assert-Eq $row.recall 0.5 'avg recall'
Assert-Eq $row.clean_fp 0.5 'avg clean_fp'

Remove-Item $tmp -Recurse -Force
Write-Host ""
if ($fail -eq 0) { Write-Host "ALL TESTS PASSED"; exit 0 }
else { Write-Host ("$fail ASSERTION(S) FAILED"); exit 1 }
