# Runs every case against every model, N passes each (reviews are non-deterministic).
# Usage: ./run.ps1                                   # defaults below
#        ./run.ps1 -Models claude-opus-4-8,claude-opus-5 -Passes 3
[CmdletBinding()]
param(
    [string[]]$Models = @('claude-opus-4-8', 'claude-opus-5'),
    [int]$Passes = 3,
    [string[]]$CasePattern = @('*'),
    [ValidateSet('strict', 'loose')][string]$PromptMode = 'strict'
)
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$reviewer = Join-Path $root 'reviewer.ps1'
$cases = Get-ChildItem -Path (Join-Path $root 'cases') -Directory |
    Where-Object { $n = $_.Name; @($CasePattern | Where-Object { $n -like $_ }).Count -gt 0 } |
    Sort-Object Name

$total = $Models.Count * $Passes * $cases.Count
$i = 0
foreach ($model in $Models) {
    foreach ($pass in 1..$Passes) {
        foreach ($case in $cases) {
            $i++
            $outDir = Join-Path $root "results/$PromptMode/$model/pass$pass"
            $out = Join-Path $outDir "$($case.Name).json"
            Write-Host ("[{0}/{1}] {2} {3} pass{4} {5}" -f $i, $total, $PromptMode, $model, $pass, $case.Name)
            try {
                & $reviewer -CaseDir $case.FullName -Model $model -OutFile $out -PromptMode $PromptMode
            } catch {
                Write-Warning "  failed: $($_.Exception.Message)"
            }
        }
    }
}
Write-Host ""
Write-Host "Done. Score with:  ./score.ps1   (or: python ./score.py if real Python is installed)"
