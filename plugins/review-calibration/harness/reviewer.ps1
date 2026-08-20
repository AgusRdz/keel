# Runs ONE review case against ONE model, headless, and writes normalized findings JSON.
# Usage: ./reviewer.ps1 -CaseDir <dir> -Model <id> -OutFile <path>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$CaseDir,
    [Parameter(Mandatory)][string]$Model,
    [Parameter(Mandatory)][string]$OutFile,
    [ValidateSet('strict', 'loose')][string]$PromptMode = 'strict'
)
$ErrorActionPreference = 'Stop'

$beforeFile = Get-ChildItem -Path $CaseDir -Filter 'before.*' | Select-Object -First 1
$afterFile  = Get-ChildItem -Path $CaseDir -Filter 'after.*'  | Select-Object -First 1
if (-not $afterFile) { throw "No after.* file in $CaseDir" }

$before = if ($beforeFile) { Get-Content -Raw $beforeFile.FullName } else { '' }
$after  = Get-Content -Raw $afterFile.FullName

# Two prompt modes. STRICT mirrors the Calibration contract (repro required,
# correctness/security/data-loss floor) = the reviewer as you'd deploy it. LOOSE is a
# generic "comment on anything" prompt with no floor = the reviewer running on model
# defaults, to isolate how much each model nitpicks WITHOUT calibration.
if ($PromptMode -eq 'loose') {
    $prompt = @"
You are a code reviewer. Review the CHANGE from BEFORE to AFTER and report anything
worth raising -- bugs, risks, style, maintainability, naming, performance, anything you
would comment on in a pull request.

Return ONLY minified JSON. No prose, no markdown, no code fences. Exact shape:
{"findings":[{"line":<int line number in AFTER>,"type":"<short-kebab>","severity":"<your call>","repro":"<why it matters>"}]}

=== BEFORE ===
$before
=== AFTER ===
$after
"@
}
else {
    $prompt = @"
You are a senior code reviewer. Review the CHANGE from BEFORE to AFTER for defects.
Report a finding ONLY when you can state a concrete failure (specific input -> wrong result).
Severity floor: correctness, security, data-loss. Do NOT report style, naming, formatting,
or preference. If the change is behavior-preserving and correct, return an empty array.

Return ONLY minified JSON. No prose, no markdown, no code fences. Exact shape:
{"findings":[{"line":<int line number in AFTER>,"type":"<short-kebab>","severity":"correctness|security|data-loss","repro":"<input -> wrong output>"}]}

=== BEFORE ===
$before
=== AFTER ===
$after
"@
}

$raw = & claude -p $prompt --model $Model 2>$null | Out-String

# Extract the first {...last} JSON object, tolerating stray prose or fences.
$json = [regex]::Match($raw, '(?s)\{.*\}').Value
$result = $null
if ($json) {
    try { $result = $json | ConvertFrom-Json } catch { $result = $null }
}
if ($null -eq $result) {
    $result = [pscustomobject]@{ findings = @(); parse_error = $true; raw = $raw.Trim() }
}
if (-not ($result.PSObject.Properties.Name -contains 'findings')) {
    $result | Add-Member -NotePropertyName findings -NotePropertyValue @()
}

$dir = Split-Path -Parent $OutFile
if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
$result | ConvertTo-Json -Depth 8 | Set-Content -Path $OutFile -Encoding utf8
