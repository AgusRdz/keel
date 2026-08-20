"""Scoring library for review-eval. Pure functions, no side effects on import.
Stdlib-only Python port of lib/scoring.ps1. Consumed by ../run.py, ../score.py and
../../tests/test-score.py / test-run.py.
"""
import json
from pathlib import Path


def case_identity(cases_dir, case_dir):
    """Case identity = case_dir's path relative to cases_dir, forward-slash separated
    (e.g. 'csharp/01-null-deref', 'python/21-mutable-default-arg'). Single source of
    truth for identity everywhere: results filenames, truth keys, --case-pattern."""
    rel = Path(case_dir).resolve().relative_to(Path(cases_dir).resolve())
    return rel.as_posix()


def discover_case_dirs(cases_dir):
    """Recursive discovery: a case is ANY directory at any depth under cases_dir that
    contains a truth.json. No hardcoded language list. Returns a sorted (by identity)
    list of Path objects."""
    cases_dir = Path(cases_dir)
    if not cases_dir.is_dir():
        return []
    dirs = [p.parent for p in cases_dir.rglob("truth.json") if p.is_file()]
    dirs.sort(key=lambda d: case_identity(cases_dir, d))
    return dirs


def load_truth(cases_dir):
    """Load truth.json for every case dir under cases_dir (recursive), keyed by case
    identity, sorted. Returns an ordinary dict (insertion order == sorted order,
    matching the [ordered] hashtable Get-Truth builds)."""
    cases_dir = Path(cases_dir)
    truth = {}
    for d in discover_case_dirs(cases_dir):
        identity = case_identity(cases_dir, d)
        with open(d / "truth.json", "r", encoding="utf-8") as f:
            truth[identity] = json.load(f)
    return truth


def pass_score(truth, pass_dir, window=3):
    """Score a single pass directory (one model, one pass) against ground truth.

    A planted bug counts as caught if any finding lands within +/-window lines
    (same file is assumed; cases are single-file). Mirrors Get-PassScore exactly:
    clean cases contribute their raw findings count to clean_fp; for buggy cases,
    every finding not within window of any planted bug counts as buggy_unmatched.
    """
    pass_dir = Path(pass_dir)
    planted = 0
    caught = 0
    clean_fp = 0
    unmatched = 0

    for case, t in truth.items():
        file_path = pass_dir / "{}.json".format(case)
        findings = []
        if file_path.is_file():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                raw_findings = data.get("findings") if isinstance(data, dict) else None
                if isinstance(raw_findings, list):
                    findings = raw_findings
            except Exception:
                findings = []

        lines = [
            int(f["line"])
            for f in findings
            if isinstance(f, dict) and f.get("line") is not None
        ]

        if t.get("clean"):
            clean_fp += len(findings)
            continue

        bugs = t.get("bugs") or []
        planted += len(bugs)
        for b in bugs:
            if any(abs(l - b["line"]) <= window for l in lines):
                caught += 1
        for l in lines:
            if not any(abs(l - b["line"]) <= window for b in bugs):
                unmatched += 1

    return {
        "recall": (caught / planted) if planted else 0.0,
        "clean_fp": clean_fp,
        "buggy_unmatched": unmatched,
        "planted": planted,
        "caught": caught,
    }


def model_scores(truth, results_mode_dir, window=3):
    """Aggregate every model under a results/<mode> directory, averaging pass_score
    across its pass* subdirectories. Mirrors Get-ModelScores."""
    results_mode_dir = Path(results_mode_dir)
    rows = []
    if not results_mode_dir.is_dir():
        return rows

    for m in sorted(results_mode_dir.iterdir(), key=lambda p: p.name):
        if not m.is_dir():
            continue
        passes = sorted(
            (p for p in m.iterdir() if p.is_dir() and p.name.startswith("pass")),
            key=lambda p: p.name,
        )
        if not passes:
            continue
        agg = [pass_score(truth, p, window=window) for p in passes]
        n = len(agg)
        rows.append(
            {
                "model": m.name,
                "passes": n,
                "recall": sum(a["recall"] for a in agg) / n,
                "clean_fp": sum(a["clean_fp"] for a in agg) / n,
                "buggy_unmatched": sum(a["buggy_unmatched"] for a in agg) / n,
            }
        )
    return rows
