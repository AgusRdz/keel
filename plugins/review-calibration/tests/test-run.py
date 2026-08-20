#!/usr/bin/env python
"""Deterministic self-test for harness/run.py. NO subprocess, NO model calls, NO
network. Exercises the pure functions only: extract_json, normalize, build_prompt,
discover_cases, result_path. Stdlib only.

Run: python ./tests/test-run.py   (exit 0 = pass, 1 = fail)
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))
import run  # noqa: E402

fail = 0


def check(condition, label):
    global fail
    if condition:
        print("  PASS  {}".format(label))
    else:
        print("  FAIL  {}".format(label))
        fail += 1


def eq(actual, expected, label):
    check(actual == expected, "{}  (got {!r})".format(label, actual))


# --- extract_json ------------------------------------------------------------
print("extract_json")
eq(run.extract_json('{"findings":[]}'), '{"findings":[]}', "clean JSON")

raw_prose = 'Sure, here you go:\n```json\n{"findings":[{"line":4,"type":"x"}]}\n```\nHope that helps!'
eq(
    run.extract_json(raw_prose),
    '{"findings":[{"line":4,"type":"x"}]}',
    "JSON surrounded by prose/fences",
)

eq(run.extract_json("no json here at all"), None, "non-JSON returns None")
eq(run.extract_json(""), None, "empty string returns None")

# Multi-object text: greedy DOTALL match should span first '{' to LAST '}'.
multi = '{"a":1} some text {"b":2}'
eq(run.extract_json(multi), '{"a":1} some text {"b":2}', "greedy span from first { to last }")

# --- normalize ----------------------------------------------------------------
print("normalize")
eq(run.normalize({"findings": [{"line": 1}]}, "raw"), {"findings": [{"line": 1}]}, "findings key preserved")
eq(run.normalize({"other": 1}, "raw"), {"other": 1, "findings": []}, "missing findings key added")
eq(
    run.normalize(None, "  some raw output  "),
    {"findings": [], "parse_error": True, "raw": "some raw output"},
    "parse failure -> parse_error + trimmed raw",
)
eq(
    run.normalize(["not", "a", "dict"], "raw text"),
    {"findings": [], "parse_error": True, "raw": "raw text"},
    "non-dict parsed value treated as parse failure",
)

# --- build_prompt ---------------------------------------------------------
print("build_prompt")
before_txt = "int Foo() { return 1; }"
after_txt = "int Foo() { return 2; }"
contract_txt = "Report a finding ONLY when you can state a concrete failure."

strict_prompt = run.build_prompt("strict", contract_txt, before_txt, after_txt)
check(contract_txt in strict_prompt, "strict prompt contains injected contract text")
check("=== BEFORE ===" in strict_prompt and before_txt in strict_prompt, "strict prompt contains BEFORE")
check("=== AFTER ===" in strict_prompt and after_txt in strict_prompt, "strict prompt contains AFTER")
check("senior code reviewer" in strict_prompt, "strict prompt uses strict wording")

loose_prompt = run.build_prompt("loose", contract_txt, before_txt, after_txt)
check(contract_txt not in loose_prompt, "loose prompt does NOT contain the contract text")
check("=== BEFORE ===" in loose_prompt and before_txt in loose_prompt, "loose prompt contains BEFORE")
check("=== AFTER ===" in loose_prompt and after_txt in loose_prompt, "loose prompt contains AFTER")
check("anything you\nwould comment on in a pull request" in loose_prompt, "loose prompt uses loose wording")

# --- discover_cases + result_path -------------------------------------------
print("discover_cases + result_path")
tmp = Path(tempfile.mkdtemp(prefix="review-eval-runtest-"))
try:
    cases_dir = tmp / "cases"
    for name in ["01-alpha", "02-beta", "10-gamma", "not-a-case.txt"]:
        p = cases_dir / name
        if name.endswith(".txt"):
            cases_dir.mkdir(parents=True, exist_ok=True)
            (cases_dir / name).write_text("x", encoding="utf-8")
        else:
            p.mkdir(parents=True, exist_ok=True)
            (p / "before.cs").write_text("before", encoding="utf-8")
            (p / "after.cs").write_text("after", encoding="utf-8")
            (p / "truth.json").write_text(json.dumps({"clean": True}), encoding="utf-8")

    all_cases = run.discover_cases(cases_dir, ["*"])
    eq([c.name for c in all_cases], ["01-alpha", "02-beta", "10-gamma"], "default '*' matches all case dirs, sorted, skips files")

    filtered = run.discover_cases(cases_dir, ["0*"])
    eq([c.name for c in filtered], ["01-alpha", "02-beta"], "glob pattern filters by directory name")

    multi = run.discover_cases(cases_dir, ["01-*", "10-*"])
    eq([c.name for c in multi], ["01-alpha", "10-gamma"], "multiple patterns OR together")

    ci = run.discover_cases(cases_dir, ["01-ALPHA"])
    eq([c.name for c in ci], ["01-alpha"], "pattern matching is case-insensitive (like PowerShell -like)")

    none_dir = run.discover_cases(tmp / "does-not-exist", ["*"])
    eq(none_dir, [], "missing cases_dir returns empty list")

    rp = run.result_path(tmp, "strict", "claude-opus-4-8", 2, "01-alpha")
    expected = tmp / "results" / "strict" / "claude-opus-4-8" / "pass2" / "01-alpha.json"
    eq(rp, expected, "result_path builds results/<mode>/<model>/pass<N>/<case>.json")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print()
if fail == 0:
    print("ALL TESTS PASSED")
    sys.exit(0)
else:
    print("{} ASSERTION(S) FAILED".format(fail))
    sys.exit(1)
