"""
run_eval.py — End-to-end eval runner for the lhs-sampler skill.

Asserts on fields of the trace JSON the skill produces. No LLM-as-judge.

Modes:
    --mode=dry-run : print what would be asserted for each case.
    --mode=replay  : find the latest trace for each case and assert.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


EVAL_CASES = Path(__file__).parent / "eval_cases.json"
TRACES_DIR = Path(__file__).parent.parent / "traces"


@dataclass
class CaseResult:
    case_id: str
    passed: bool
    failures: list[str]
    trace_path: Optional[Path]


def load_cases() -> list[dict]:
    with open(EVAL_CASES, "r") as f:
        data = json.load(f)
    return data["cases"]


def find_trace_for_case(case_id: str, traces_dir: Path = TRACES_DIR) -> Optional[Path]:
    if not traces_dir.exists():
        return None
    matches: list[tuple[float, Path]] = []
    for p in traces_dir.glob("*.json"):
        try:
            with open(p, "r") as f:
                trace = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        if trace.get("case_id") == case_id:
            matches.append((p.stat().st_mtime, p))
    if not matches:
        return None
    matches.sort(reverse=True)
    return matches[0][1]


def assert_trace_matches(expect: dict, trace: dict) -> list[str]:
    failures: list[str] = []
    for k, v in expect.items():
        if k.startswith("_"):
            continue

        if k == "parsed":
            sub = trace.get("parsed", {})
            if not isinstance(sub, dict):
                failures.append(f"parsed: expected dict, got {type(sub).__name__}")
                continue
            for pk, pv in v.items():
                if sub.get(pk) != pv:
                    failures.append(f"parsed.{pk}: expected {pv!r}, got {sub.get(pk)!r}")
            continue

        if k == "csv_path_pattern":
            actual = trace.get("csv_path")
            if not actual or v not in actual:
                failures.append(f"csv_path: expected substring {v!r}, got {actual!r}")
            continue

        if k == "nearby_alternatives_at_dim":
            actual = trace.get("nearby_alternatives")
            if list(actual or []) != list(v):
                failures.append(f"nearby_alternatives: expected {v!r}, got {actual!r}")
            continue

        if k not in trace:
            failures.append(f"{k}: missing from trace (expected {v!r})")
            continue

        if trace[k] != v:
            failures.append(f"{k}: expected {v!r}, got {trace[k]!r}")

    return failures


def run_case(case: dict, traces_dir: Path = TRACES_DIR) -> CaseResult:
    case_id = case["id"]
    trace_path = find_trace_for_case(case_id, traces_dir)
    if trace_path is None:
        return CaseResult(case_id, False, ["no trace found"], None)
    with open(trace_path, "r") as f:
        trace = json.load(f)
    failures = assert_trace_matches(case["expect"], trace)
    return CaseResult(case_id, not failures, failures, trace_path)


def run_all(traces_dir: Path = TRACES_DIR) -> list[CaseResult]:
    return [run_case(c, traces_dir) for c in load_cases()]


def print_report(results: list[CaseResult]) -> int:
    failed = 0
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.case_id}")
        if not r.passed:
            failed += 1
            for f in r.failures:
                print(f"    - {f}")
    total = len(results)
    print(f"\n{total - failed}/{total} passed")
    return 0 if failed == 0 else 1


def _print_dry_run(cases: list[dict]) -> int:
    for c in cases:
        asserted = [k for k in c["expect"].keys() if not k.startswith("_")]
        print(f"[{c['id']}] {c['prompt']}")
        print(f"    asserts: {', '.join(asserted)}")
    print(f"\n{len(cases)} cases")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["replay", "dry-run"], default="replay")
    p.add_argument("--traces-dir", type=Path, default=TRACES_DIR)
    args = p.parse_args(argv)

    if args.mode == "dry-run":
        return _print_dry_run(load_cases())

    results = run_all(traces_dir=args.traces_dir)
    return print_report(results)


if __name__ == "__main__":
    sys.exit(main())
