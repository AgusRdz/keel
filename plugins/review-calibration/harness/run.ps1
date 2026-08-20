# Runs every case against every model, N passes each (reviews are non-deterministic).
# Usage: ./run.ps1                                   # defaults below
#        ./run.ps1 -Models claude-opus-4-8,claude-opus-5 -Passes 3
[CmdletBinding()]
param(
    [string[]]$Models = @('claude-opus-4-8', 'claude-opus-5'),
    [int]$Passes = 3,
    [string[]]$CasePattern = @('*'),
    [ValidateSet('strict', 'loose')][string]$PromptMode = 'strict',
    [string]$Contract = (Join-Path $PSScriptRoot '..\contract\calibration-rules.md')
)
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$reviewer = Join-Path $root 'reviewer.ps1'
. (Join-Path $root 'lib/scoring.ps1')

$casesDir = Join-Path $root 'cases'
# Case identity = path relative to cases/, forward slashes (e.g. 'csharp/01-null-deref').
# --case-pattern matches against either the full identity or just the leaf dir name,
# so both 'csharp/01-*' and '01-*' work; matching is case-insensitive (-like semantics).
$cases = Get-CaseDirs -CasesDir $casesDir | ForEach-Object {
    [pscustomobject]@{
        FullName = $_.FullName
        Identity = Get-CaseIdentity -CasesDir $casesDir -CaseDir $_.FullName
        Leaf     = $_.Name
    }
} | Where-Object {
    $id = $_.Identity; $leaf = $_.Leaf
    @($CasePattern | Where-Object { $id -like $_ -or $leaf -like $_ }).Count -gt 0
} | Sort-Object Identity

$total = $Models.Count * $Passes * $cases.Count
$i = 0
foreach ($model in $Models) {
    foreach ($pass in 1..$Passes) {
        foreach ($case in $cases) {
            $i++
            $outDir = Join-Path $root "results/$PromptMode/$model/pass$pass"
            $out = Join-Path $outDir "$($case.Identity).json"
            Write-Host ("[{0}/{1}] {2} {3} pass{4} {5}" -f $i, $total, $PromptMode, $model, $pass, $case.Identity)
            try {
                & $reviewer -CaseDir $case.FullName -Model $model -OutFile $out -PromptMode $PromptMode -Contract $Contract
            } catch {
                Write-Warning "  failed: $($_.Exception.Message)"
            }
        }
    }
}
Write-Host ""
Write-Host "Done. Score with:  ./score.ps1   (or: python ./score.py if real Python is installed)"
