# Scoring library for review-eval. Pure functions, no side effects on dot-source.
# Consumed by ../score.ps1 and ../../tests/test-score.ps1.

function Get-Truth {
    param([Parameter(Mandatory)][string]$CasesDir)
    $truth = [ordered]@{}
    foreach ($d in Get-ChildItem $CasesDir -Directory | Sort-Object Name) {
        $tp = Join-Path $d.FullName 'truth.json'
        if (Test-Path $tp) { $truth[$d.Name] = Get-Content $tp -Raw | ConvertFrom-Json }
    }
    return $truth
}

# Score a single pass directory (one model, one pass) against ground truth.
# A planted bug counts as caught if any finding lands within +/-Window lines (same file
# is assumed; cases are single-file). Returns recall / clean_fp / buggy_unmatched.
function Get-PassScore {
    param(
        [Parameter(Mandatory)]$Truth,
        [Parameter(Mandatory)][string]$PassDir,
        [int]$Window = 3
    )
    $planted = 0; $caught = 0; $cleanFp = 0; $unmatched = 0
    foreach ($case in $Truth.Keys) {
        $t = $Truth[$case]
        $file = Join-Path $PassDir "$case.json"
        $findings = @()
        if (Test-Path $file) {
            try {
                $data = Get-Content $file -Raw | ConvertFrom-Json
                if ($data.findings) { $findings = @($data.findings) }
            } catch { }
        }
        $lines = @($findings | Where-Object { $null -ne $_.line } | ForEach-Object { [int]$_.line })
        if ($t.clean) { $cleanFp += $findings.Count; continue }
        $bugs = @($t.bugs); $planted += $bugs.Count
        foreach ($b in $bugs) {
            $hit = $false
            foreach ($l in $lines) { if ([math]::Abs($l - $b.line) -le $Window) { $hit = $true; break } }
            if ($hit) { $caught++ }
        }
        foreach ($l in $lines) {
            $matched = $false
            foreach ($b in $bugs) { if ([math]::Abs($l - $b.line) -le $Window) { $matched = $true; break } }
            if (-not $matched) { $unmatched++ }
        }
    }
    [pscustomobject]@{
        recall          = if ($planted) { $caught / $planted } else { 0.0 }
        clean_fp        = $cleanFp
        buggy_unmatched = $unmatched
        planted         = $planted
        caught          = $caught
    }
}

# Aggregate every model under a results/<mode> directory, averaging across passes.
function Get-ModelScores {
    param(
        [Parameter(Mandatory)]$Truth,
        [Parameter(Mandatory)][string]$ResultsModeDir,
        [int]$Window = 3
    )
    $rows = @()
    if (Test-Path $ResultsModeDir) {
        foreach ($m in Get-ChildItem $ResultsModeDir -Directory | Sort-Object Name) {
            $passes = @(Get-ChildItem $m.FullName -Directory -Filter 'pass*' | Sort-Object Name)
            if ($passes.Count -eq 0) { continue }
            $agg = @(foreach ($p in $passes) { Get-PassScore -Truth $Truth -PassDir $p.FullName -Window $Window })
            $rows += [pscustomobject]@{
                model           = $m.Name
                passes          = $agg.Count
                recall          = ($agg | Measure-Object recall -Average).Average
                clean_fp        = ($agg | Measure-Object clean_fp -Average).Average
                buggy_unmatched = ($agg | Measure-Object buggy_unmatched -Average).Average
            }
        }
    }
    return $rows
}
