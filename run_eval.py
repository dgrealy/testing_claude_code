"""
run_eval.py — End-to-end eval runner for the lhs-sampler skill.

This is the "structural" eval layer: it asserts on fields of the trace JSON
that the skill produces. It does NOT use an LLM-as-judge — output is
structured enough that `assert` suffices. Quality of clarification *prose*
is reviewed separately (manually, via spot-check).

How it's used:
    Since the parsing happens inside Claude (the L step), this runner is NOT
    a fully automated pytest. It is the harness for a manual or semi-manual
    eval pass: run Claude-with-the-skill against each prompt in
    eval_cases.json, collect the traces it writes, then run this script to
    assert each trace against the expected fields.

Two modes:
    1. `--mode=replay`: read traces from ../traces/ that match each case's id
       and assert against eval_cases.json. Use this after a manual eval pass.
    2. `--mode=dry-run`: just print what would be asserted for each case.
       Useful for sanity-checking the eval set itself.

Run: python evals/run_eval.py --mode=replay
     python evals/run_eval.py --mode=dry-run

Implementation status: STUB. Fill in the TODOs.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


EVAL_CASES = Path(__file__).parent / "eval_cases.json"
TRACES_DIR = Path(__file__).parent.parent / "traces"


@dataclass
class CaseResult:
    case_id: str
    passed: bool
    failures: list[str]  # list of human-readable failure messages
    trace_path: Optional[Path]


def load_cases() -> list[dict]:
    """Load eval_cases.json and return the list of cases (top-level 'cases' key)."""
    # TODO: implement.
    raise NotImplementedError


def find_trace_for_case(case_id: str, traces_dir: Path = TRACES_DIR) -> Optional[Path]:
    """Find the most recent trace file tagged with this case_id.

    Convention: when running the eval, the skill should write traces with the
    case_id encoded in the filename or in a `case_id` field. For now, scan
    traces_dir for any JSON containing `"case_id": "<case_id>"` and return
    the most recently modified match.
    """
    # TODO: implement.
    # Iterate traces_dir.glob('*.json'), load each, filter by case_id field,
    # return max by mtime. Return None if no match.
    raise NotImplementedError


def assert_trace_matches(expect: dict, trace: dict) -> list[str]:
    """Compare expected fields against the trace.

    Returns a list of failure messages (empty == pass).

    Special handling:
        - `parsed` is checked field-by-field, not as a whole dict (so unrelated
          parsed fields don't cause spurious failures).
        - `csv_path_pattern` checks the trace's `csv_path` matches a path
          pattern with a substring match.
        - `nearby_alternatives_at_dim` checks the list equals exactly,
          preserving order (order encodes distance ranking).
        - Keys in `expect` that start with `_` (like `_critical`) are
          ignored — they're notes for humans.
        - Keys in `expect` that aren't in `trace` are reported as missing.
    """
    # TODO: implement.
    raise NotImplementedError


def run_case(case: dict, traces_dir: Path = TRACES_DIR) -> CaseResult:
    """Find the trace for a case and assert against expectations."""
    # TODO: implement.
    raise NotImplementedError


def run_all(traces_dir: Path = TRACES_DIR) -> list[CaseResult]:
    """Run every case in eval_cases.json. Return list of results."""
    # TODO: implement.
    raise NotImplementedError


def print_report(results: list[CaseResult]) -> int:
    """Print a summary report. Returns exit code (0 if all pass, 1 if any fail)."""
    # TODO: implement.
    # For each result: print id, PASS/FAIL, failures.
    # At the end: print "X/Y passed". Group failures by category for readability.
    raise NotImplementedError


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["replay", "dry-run"], default="replay")
    p.add_argument("--traces-dir", type=Path, default=TRACES_DIR)
    args = p.parse_args(argv)

    if args.mode == "dry-run":
        # TODO: print each case's id, prompt, and what fields would be asserted.
        # No trace lookups, no Claude calls.
        raise NotImplementedError

    results = run_all(traces_dir=args.traces_dir)
    return print_report(results)


if __name__ == "__main__":
    sys.exit(main())
