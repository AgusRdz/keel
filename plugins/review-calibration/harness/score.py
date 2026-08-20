#!/usr/bin/env python
"""Scores review-eval results against ground truth. Stdlib only. Rewritten to parity
with score.ps1 (lib/scoring.ps1's logic lives in lib/scoring.py; this file just wires
CLI args + printing, mirroring score.ps1's table and footer exactly).

Usage:
    python score.py [--mode strict|loose|both] [--window 3]
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "lib"))
import scoring  # noqa: E402  (import after sys.path tweak, mirrors ". lib/scoring.ps1")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Score review-eval results against ground truth.")
    parser.add_argument("--mode", choices=["strict", "loose", "both"], default="strict")
    parser.add_argument("--window", type=int, default=3)
    args = parser.parse_args(argv)

    truth = scoring.load_truth(ROOT / "cases")
    n_clean = sum(1 for t in truth.values() if t.get("clean"))
    n_buggy = len(truth) - n_clean
    modes = ["strict", "loose"] if args.mode == "both" else [args.mode]

    print()
    print(
        "review-eval  |  cases: {} ({} buggy, {} clean)  |  window: +/-{} lines".format(
            len(truth), n_buggy, n_clean, args.window
        )
    )

    fmt = "{:<24} {:>6} {:>8} {:>13} {:>14} {:>16}"
    for mode in modes:
        rows = scoring.model_scores(truth, ROOT / "results" / mode, window=args.window)
        print()
        print("=== PROMPT MODE: {} ===".format(mode.upper()))
        if not rows:
            print("  (no results -- run: ./run.sh --prompt-mode {})".format(mode))
            continue
        print(fmt.format("model", "passes", "recall", "clean-FP/run", "nitpick/clean", "buggy-unmatched"))
        print("-" * 86)
        for r in rows:
            nitpick = (r["clean_fp"] / n_clean) if n_clean else 0.0
            print(
                fmt.format(
                    r["model"],
                    r["passes"],
                    "{:.0f}%".format(r["recall"] * 100),
                    "{:.1f}".format(r["clean_fp"]),
                    "{:.2f}".format(nitpick),
                    "{:.1f}".format(r["buggy_unmatched"]),
                )
            )

    print()
    print("Higher recall = better.  Lower clean-FP/run = better (the 'nitpicky' number).")
    print("strict->loose delta = how much each model nitpicks WITHOUT the Calibration prompt.")


if __name__ == "__main__":
    sys.exit(main() or 0)
