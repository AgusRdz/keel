#!/usr/bin/env python
"""Deterministic self-test for harness/lib/scoring.py. NO model calls, NO network.
Mirrors the scenarios in tests/test-score.ps1. Stdlib only.

Run: python ./tests/test-score.py   (exit 0 = pass, 1 = fail)
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness" / "lib"))
import scoring  # noqa: E402

fail = 0


def assert_eq(actual, expected, label):
    global fail
    ok = abs(float(actual) - float(expected)) < 1e-9
    if ok:
        print("  PASS  {}  (= {})".format(label, actual))
    else:
        print("  FAIL  {}  expected {}, got {}".format(label, expected, actual))
        fail += 1


# Synthetic ground truth: one buggy case (bug at line 10), one clean case.
truth = {
    "a-bug": {"clean": False, "bugs": [{"file": "after.cs", "line": 10}]},
    "b-clean": {"clean": True, "bugs": []},
}

tmp = Path(tempfile.mkdtemp(prefix="review-eval-selftest-"))


def write_findings(dir_path, case, lines):
    dir_path = Path(dir_path)
    dir_path.mkdir(parents=True, exist_ok=True)
    findings = [{"line": l, "type": "t", "severity": "correctness", "repro": "r"} for l in lines]
    with open(dir_path / "{}.json".format(case), "w", encoding="utf-8") as f:
        json.dump({"findings": findings}, f)


try:
    # --- Scenario 1: bug caught (finding at 11, within +/-3 of 10); clean case has 1 FP ---
    p1 = tmp / "pass1"
    write_findings(p1, "a-bug", [11])
    write_findings(p1, "b-clean", [2])
    s1 = scoring.pass_score(truth, p1, window=3)
    print("Scenario 1: bug caught within window, one clean FP")
    assert_eq(s1["recall"], 1.0, "recall")
    assert_eq(s1["clean_fp"], 1, "clean_fp")
    assert_eq(s1["buggy_unmatched"], 0, "buggy_unmatched")

    # --- Scenario 2: bug MISSED (finding at 20, outside window); clean case silent ---
    p2 = tmp / "pass2"
    write_findings(p2, "a-bug", [20])
    write_findings(p2, "b-clean", [])
    s2 = scoring.pass_score(truth, p2, window=3)
    print("Scenario 2: bug missed (out of window), clean silent")
    assert_eq(s2["recall"], 0.0, "recall")
    assert_eq(s2["clean_fp"], 0, "clean_fp")
    assert_eq(s2["buggy_unmatched"], 1, "buggy_unmatched")

    # --- Scenario 3: window boundary is inclusive (finding at 13, exactly +3 of 10) ---
    p3 = tmp / "pass3"
    write_findings(p3, "a-bug", [13])
    write_findings(p3, "b-clean", [])
    s3 = scoring.pass_score(truth, p3, window=3)
    print("Scenario 3: finding exactly at window edge counts as caught")
    assert_eq(s3["recall"], 1.0, "recall (edge inclusive)")

    # --- Scenario 4: multi-pass aggregation averages across passes ---
    mdir = tmp / "model-x"
    write_findings(mdir / "pass1", "a-bug", [10])  # caught -> recall 1.0
    write_findings(mdir / "pass1", "b-clean", [1])  # 1 FP
    write_findings(mdir / "pass2", "a-bug", [99])  # missed -> recall 0.0
    write_findings(mdir / "pass2", "b-clean", [])  # 0 FP
    rows = scoring.model_scores(truth, tmp, window=3)
    row = next(r for r in rows if r["model"] == "model-x")
    print("Scenario 4: aggregation averages recall (1.0,0.0)->0.5 and clean_fp (1,0)->0.5")
    assert_eq(row["passes"], 2, "passes")
    assert_eq(row["recall"], 0.5, "avg recall")
    assert_eq(row["clean_fp"], 0.5, "avg clean_fp")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print()
if fail == 0:
    print("ALL TESTS PASSED")
    sys.exit(0)
else:
    print("{} ASSERTION(S) FAILED".format(fail))
    sys.exit(1)
