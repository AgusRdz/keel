#!/usr/bin/env python3
"""Behavior-eval runner: does the calibration block actually change agent behavior?

For each (arm, probe, run) it builds an isolated workdir seeded with the probe's files
plus the arm's project CLAUDE.md, runs `claude -p <task>` there with edits auto-accepted,
then records what the agent CHANGED on disk (a unified diff vs the seed -- ground truth,
not the agent's self-report) and its written reply. Results land in
runs/<arm>/<probe>/run<N>/result.json. Score them with score.py.

Arms:
  control   -- project CLAUDE.md re-adds the calibration block  -> calibrated
  treatment -- project CLAUDE.md has no rules                    -> un-calibrated
The user's global ~/.claude/CLAUDE.md loads in BOTH arms, so it cancels; the only
variable between arms is the block. Stdlib only, Python 3.8+.

Usage:
  python run.py                                  # all arms, all probes, 3 runs each
  python run.py --arms treatment --runs 5
  python run.py --probes 01-rename-scope,02-add-divide --model claude-opus-4-8
"""
import argparse
import difflib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROBES_DIR = ROOT / "probes"
ARMS_DIR = ROOT / "arms"
RUNS_DIR = ROOT / "runs"

DEFAULT_MODEL = "claude-opus-4-8"
DEFAULT_ARMS = ["control", "treatment"]
DEFAULT_RUNS = 3


def read_text(p):
    return Path(p).read_text(encoding="utf-8", errors="replace")


def discover_probes(patterns):
    out = []
    for d in sorted(PROBES_DIR.iterdir()):
        if d.is_dir() and (d / "task.txt").is_file():
            if not patterns or d.name in patterns:
                out.append(d)
    return out


def seed_snapshot(seed_dir):
    """Map {relpath -> text} for every file under the probe's seed/ dir."""
    snap = {}
    if seed_dir.is_dir():
        for p in sorted(seed_dir.rglob("*")):
            if p.is_file():
                snap[p.relative_to(seed_dir).as_posix()] = read_text(p)
    return snap


def build_workdir(workdir, seed, arm_claude):
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)
    for rel, text in seed.items():
        dest = workdir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
    (workdir / "CLAUDE.md").write_text(arm_claude, encoding="utf-8")


def compute_diff(seed, workdir):
    """Unified diff of workdir vs seed, ignoring the arm's CLAUDE.md. NEW/DELETED noted."""
    chunks = []
    for p in sorted(workdir.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(workdir).as_posix()
        if rel == "CLAUDE.md":
            continue
        new = read_text(p)
        old = seed.get(rel)
        if old is None:
            chunks.append("--- NEW FILE: {} ---\n{}".format(rel, new))
        elif old != new:
            d = difflib.unified_diff(
                old.splitlines(), new.splitlines(),
                fromfile=rel + " (seed)", tofile=rel + " (after)", lineterm="",
            )
            chunks.append("\n".join(d))
    for rel in seed:
        if not (workdir / rel).is_file():
            chunks.append("--- DELETED FILE: {} ---".format(rel))
    return "\n\n".join(chunks) if chunks else "(no file changes)"


def run_claude(task, model, workdir):
    exe = shutil.which("claude")
    if not exe:
        raise RuntimeError("claude CLI not found on PATH")
    proc = subprocess.run(
        [exe, "-p", task, "--model", model, "--permission-mode", "acceptEdits"],
        cwd=str(workdir),
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, encoding="utf-8", errors="replace", timeout=420,
    )
    return proc.stdout or ""


def main():
    ap = argparse.ArgumentParser(description="Behavior-eval runner for calibration.")
    ap.add_argument("--arms", default=",".join(DEFAULT_ARMS))
    ap.add_argument("--probes", default="")
    ap.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    args = ap.parse_args()

    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    probe_pats = [p.strip() for p in args.probes.split(",") if p.strip()]
    probes = discover_probes(probe_pats)
    if not probes:
        print("No probes found.", file=sys.stderr)
        return 1

    arm_claude = {}
    for arm in arms:
        f = ARMS_DIR / arm / "CLAUDE.md"
        if not f.is_file():
            print("Missing arm CLAUDE.md: {}".format(f), file=sys.stderr)
            return 1
        arm_claude[arm] = read_text(f)

    total = len(arms) * len(probes) * args.runs
    i = 0
    for arm in arms:
        for probe in probes:
            seed = seed_snapshot(probe / "seed")
            task = read_text(probe / "task.txt").strip()
            for n in range(1, args.runs + 1):
                i += 1
                workdir = RUNS_DIR / arm / probe.name / "run{}".format(n)
                print("[{}/{}] {} {} run{}".format(i, total, arm, probe.name, n))
                build_workdir(workdir, seed, arm_claude[arm])
                try:
                    reply = run_claude(task, args.model, workdir)
                except Exception as e:  # noqa: BLE001
                    print("  failed: {}".format(e), file=sys.stderr)
                    reply = ""
                diff = compute_diff(seed, workdir)
                (workdir / "result.json").write_text(
                    json.dumps({
                        "arm": arm, "probe": probe.name, "run": n,
                        "model": args.model, "task": task,
                        "reply": reply, "diff": diff,
                    }, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
    print("\nDone. Score with:  python score.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
