#!/usr/bin/env python
"""Scores review-eval results against ground truth. Stdlib only (no PyYAML/pandas).

Metrics per model, averaged over passes:
  recall          - planted bugs caught (finding within +/-WINDOW lines, same intent)
  clean-FP/run    - findings raised on CLEAN cases per pass  <- your nitpick/spiral signal
  nitpick/clean   - clean-FP divided by number of clean cases
  buggy-unmatched - findings on buggy cases not matching a planted bug
                    (possible false positive, OR a real bug you did not label)
"""
import json
import os
import glob

ROOT = os.path.dirname(os.path.abspath(__file__))
CASES = os.path.join(ROOT, "cases")
RESULTS = os.path.join(ROOT, "results")
WINDOW = 3  # line-match tolerance; coarse by design (see README limits)


def load_truth():
    truth = {}
    for d in sorted(os.listdir(CASES)):
        p = os.path.join(CASES, d, "truth.json")
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                truth[d] = json.load(f)
    return truth


def load_findings(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    findings = data.get("findings") or []
    return [f for f in findings if isinstance(f, dict)]


def finding_lines(findings):
    return [f["line"] for f in findings if isinstance(f.get("line"), int)]


def score_pass(truth, pass_dir):
    planted = caught = clean_fp = buggy_unmatched = 0
    for case, t in truth.items():
        findings = load_findings(os.path.join(pass_dir, case + ".json"))
        lines = finding_lines(findings)
        if t.get("clean"):
            clean_fp += len(findings)
            continue
        bugs = t.get("bugs", [])
        planted += len(bugs)
        for b in bugs:
            if any(abs(l - b["line"]) <= WINDOW for l in lines):
                caught += 1
        for l in lines:
            if not any(abs(l - b["line"]) <= WINDOW for b in bugs):
                buggy_unmatched += 1
    return {
        "recall": caught / planted if planted else 0.0,
        "clean_fp": clean_fp,
        "buggy_unmatched": buggy_unmatched,
    }


def main():
    truth = load_truth()
    n_clean = sum(1 for t in truth.values() if t.get("clean"))
    n_buggy = len(truth) - n_clean

    models = sorted(os.listdir(RESULTS)) if os.path.isdir(RESULTS) else []
    rows = []
    for model in models:
        mdir = os.path.join(RESULTS, model)
        if not os.path.isdir(mdir):
            continue
        passes = sorted(glob.glob(os.path.join(mdir, "pass*")))
        agg = [score_pass(truth, pd) for pd in passes]
        if not agg:
            continue
        n = len(agg)
        rows.append({
            "model": model,
            "passes": n,
            "recall": sum(a["recall"] for a in agg) / n,
            "clean_fp": sum(a["clean_fp"] for a in agg) / n,
            "buggy_unmatched": sum(a["buggy_unmatched"] for a in agg) / n,
        })

    print("\nreview-eval  |  cases: %d (%d buggy, %d clean)  |  window: +/-%d lines\n"
          % (len(truth), n_buggy, n_clean, WINDOW))
    if not rows:
        print("No results yet. Run:  pwsh ./run.ps1")
        return

    hdr = "%-22s %7s %8s %13s %14s %16s" % (
        "model", "passes", "recall", "clean-FP/run", "nitpick/clean", "buggy-unmatched")
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        nitpick = r["clean_fp"] / n_clean if n_clean else 0.0
        print("%-22s %7d %7.0f%% %13.1f %14.2f %16.1f" % (
            r["model"], r["passes"], r["recall"] * 100,
            r["clean_fp"], nitpick, r["buggy_unmatched"]))

    print("\nHigher recall = better (fewer real bugs missed).")
    print("Lower clean-FP/run = better (this is the 'feels nitpicky / spirals' number).")
    print("Compare columns across models to settle upgrade decisions with data.")


if __name__ == "__main__":
    main()
