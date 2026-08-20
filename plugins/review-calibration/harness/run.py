#!/usr/bin/env python
"""Runs every case against every model, N passes each (reviews are non-deterministic).

Faithful Python port of run.ps1 + reviewer.ps1 (stdlib only, Python 3.8+). Shells out to
the `claude` CLI per (model, pass, case) triple and writes normalized findings JSON to
results/<mode>/<model>/pass<N>/<case>.json -- same layout run.ps1 produces.

Usage:
    python run.py
    python run.py --models claude-opus-4-8 --models claude-opus-5 --passes 3
    python run.py --models claude-opus-4-8,claude-opus-5 --passes 3 --prompt-mode loose

CLI flag -> run.ps1 param mapping (1:1):
    --models <id>[,<id>...]   (repeatable AND/OR comma-separated) -> -Models <string[]>
    --passes <n>                                                  -> -Passes <int>
    --prompt-mode {strict,loose}                                  -> -PromptMode
    --case-pattern <glob>      (repeatable)                        -> -CasePattern <string[]>
    --contract <path>                                              -> -Contract

Defaults match run.ps1: models = claude-opus-4-8, claude-opus-5; passes = 3;
prompt-mode = strict; case-pattern = *; contract = ../contract/calibration-rules.md
(relative to this script, same as $PSScriptRoot in run.ps1/reviewer.ps1).
"""
import argparse
import fnmatch
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_CONTRACT = ROOT / ".." / "contract" / "calibration-rules.md"

DEFAULT_MODELS = ["claude-opus-4-8", "claude-opus-5"]

# --- Prompt templates -------------------------------------------------------
# Exact wording of reviewer.ps1's two prompt modes. Placeholders are replaced with
# str.replace() (not str.format()/f-strings) so the literal JSON braces in the
# "Exact shape" lines never need escaping.

_LOOSE_TEMPLATE = """You are a code reviewer. Review the CHANGE from BEFORE to AFTER and report anything
worth raising -- bugs, risks, style, maintainability, naming, performance, anything you
would comment on in a pull request.

Return ONLY minified JSON. No prose, no markdown, no code fences. Exact shape:
{"findings":[{"line":<int line number in AFTER>,"type":"<short-kebab>","severity":"<your call>","repro":"<why it matters>"}]}

=== BEFORE ===
__BEFORE__
=== AFTER ===
__AFTER__"""

_STRICT_TEMPLATE = """You are a senior code reviewer. Review the CHANGE from BEFORE to AFTER for defects, applying
this review contract:

__CONTRACT__

Return ONLY minified JSON. No prose, no markdown, no code fences. Exact shape:
{"findings":[{"line":<int line number in AFTER>,"type":"<short-kebab>","severity":"correctness|security|data-loss","repro":"<input -> wrong output>"}]}

=== BEFORE ===
__BEFORE__
=== AFTER ===
__AFTER__"""

_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def build_prompt(mode, contract_text, before, after):
    """Build the reviewer prompt exactly as reviewer.ps1 does for the given mode.

    mode: 'strict' or 'loose'. contract_text is ignored for 'loose'.
    """
    if mode == "loose":
        template = _LOOSE_TEMPLATE
    else:
        template = _STRICT_TEMPLATE.replace("__CONTRACT__", contract_text or "")
    return template.replace("__BEFORE__", before or "").replace("__AFTER__", after or "")


def extract_json(raw):
    """Extract the first '{' through the last '}' in raw (DOTALL greedy), like
    reviewer.ps1's [regex]::Match($raw, '(?s)\\{.*\\}').Value. Returns None if no
    '{...}' span is found."""
    m = _JSON_RE.search(raw or "")
    return m.group(0) if m else None


def normalize(parsed_or_none, raw):
    """Normalize a parsed JSON value (or None on parse failure) into the result dict
    written to disk. Always guarantees a 'findings' key."""
    if isinstance(parsed_or_none, dict):
        result = dict(parsed_or_none)
        if "findings" not in result:
            result["findings"] = []
        return result
    return {"findings": [], "parse_error": True, "raw": (raw or "").strip()}


def discover_cases(cases_dir, patterns):
    """List subdirectories of cases_dir whose name matches any of patterns (glob,
    case-insensitive -- matches PowerShell's -like), sorted by name. Flat discovery
    only (no recursion) -- matches run.ps1's current behavior."""
    cases_dir = Path(cases_dir)
    if not cases_dir.is_dir():
        return []
    pats = list(patterns) if patterns else ["*"]
    pats_l = [p.lower() for p in pats]
    result = []
    for entry in sorted(cases_dir.iterdir(), key=lambda p: p.name):
        if not entry.is_dir():
            continue
        name_l = entry.name.lower()
        if any(fnmatch.fnmatch(name_l, p) for p in pats_l):
            result.append(entry)
    return result


def result_path(root, mode, model, pass_n, case_name):
    """results/<mode>/<model>/pass<N>/<case>.json under root (the harness dir)."""
    return Path(root) / "results" / mode / model / "pass{}".format(pass_n) / "{}.json".format(case_name)


def _first_match(case_dir, glob_pattern):
    matches = sorted(Path(case_dir).glob(glob_pattern))
    return matches[0] if matches else None


def call_claude(prompt, model):
    """Shell out to `claude -p <prompt> --model <id>`, capturing stdout and
    discarding stderr -- matches reviewer.ps1's `& claude -p $prompt --model $Model
    2>$null | Out-String`."""
    exe = shutil.which("claude")
    if not exe:
        raise RuntimeError("claude CLI not found on PATH")
    proc = subprocess.run(
        [exe, "-p", prompt, "--model", model],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.stdout or ""


def run_one_case(case_dir, model, pass_n, mode, contract_path, root):
    """Run one (case, model, pass) review and write the normalized result JSON."""
    before_file = _first_match(case_dir, "before.*")
    after_file = _first_match(case_dir, "after.*")
    if after_file is None:
        raise FileNotFoundError("No after.* file in {}".format(case_dir))

    before = before_file.read_text(encoding="utf-8") if before_file else ""
    after = after_file.read_text(encoding="utf-8")

    contract_text = ""
    if mode != "loose":
        contract_path = Path(contract_path)
        if not contract_path.is_file():
            raise FileNotFoundError("Contract file not found: {}".format(contract_path))
        contract_text = contract_path.read_text(encoding="utf-8").strip()

    prompt = build_prompt(mode, contract_text, before, after)
    raw = call_claude(prompt, model)

    json_str = extract_json(raw)
    parsed = None
    if json_str:
        try:
            parsed = json.loads(json_str)
        except Exception:
            parsed = None
    result = normalize(parsed, raw)

    out_path = result_path(root, mode, model, pass_n, Path(case_dir).name)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")


def _flatten_comma_or_repeat(values, default):
    if not values:
        return list(default)
    out = []
    for v in values:
        out.extend(part.strip() for part in v.split(",") if part.strip())
    return out


def build_arg_parser():
    p = argparse.ArgumentParser(description="Run review-calibration cases against models.")
    p.add_argument(
        "--models",
        action="append",
        default=None,
        help="Model id. Comma-separated and/or repeatable. Default: {}".format(",".join(DEFAULT_MODELS)),
    )
    p.add_argument("--passes", type=int, default=3, help="Passes per (model, case). Default: 3")
    p.add_argument(
        "--prompt-mode",
        choices=["strict", "loose"],
        default="strict",
        help="strict = inject the calibration contract; loose = generic no-contract prompt.",
    )
    p.add_argument(
        "--case-pattern",
        action="append",
        default=None,
        help="Glob against case directory name. Repeatable. Default: *",
    )
    p.add_argument(
        "--contract",
        default=str(DEFAULT_CONTRACT),
        help="Path to the calibration contract (strict mode only). Default: {}".format(DEFAULT_CONTRACT),
    )
    return p


def main(argv=None):
    args = build_arg_parser().parse_args(argv)

    models = _flatten_comma_or_repeat(args.models, DEFAULT_MODELS)
    case_patterns = args.case_pattern if args.case_pattern else ["*"]

    cases_dir = ROOT / "cases"
    cases = discover_cases(cases_dir, case_patterns)

    total = len(models) * args.passes * len(cases)
    i = 0
    for model in models:
        for pass_n in range(1, args.passes + 1):
            for case in cases:
                i += 1
                print("[{}/{}] {} {} pass{} {}".format(i, total, args.prompt_mode, model, pass_n, case.name))
                try:
                    run_one_case(case, model, pass_n, args.prompt_mode, args.contract, ROOT)
                except Exception as e:
                    print("  failed: {}".format(e))

    print()
    print("Done. Score with:  ./score.sh   (or: python score.py / pwsh ./score.ps1)")


if __name__ == "__main__":
    sys.exit(main() or 0)
