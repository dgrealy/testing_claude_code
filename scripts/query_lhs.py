"""
query_lhs.py — Look up a Latin hypercube design in the pickle database.

This is a deterministic (D) step. The model never invokes the lookup logic
directly — it calls this script with parsed integer params. All numeric and
key-handling logic lives here.

Contract: see ../README.md sections 3, 4, 5.
"""

from __future__ import annotations

import argparse
import json
import pickle
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


LHS_DB_PATH: Path = Path(__file__).resolve().parent.parent / "optimal_lhs_database.p"

_KEY_RE = re.compile(r"^dd(\d+)_nn(\d+)$")


@dataclass
class LookupSuccess:
    key: str
    shape: tuple[int, int]
    array: object = None
    kind: str = "success"


@dataclass
class LookupMissingSameDim:
    key_attempted: str
    n_dims: int
    requested_n_points: int
    nearby: list[int]
    kind: str = "missing_same_dim"


@dataclass
class LookupMissingNoDim:
    key_attempted: str
    n_dims: int
    available_dims: list[int]
    kind: str = "missing_no_dim"


LookupResult = LookupSuccess | LookupMissingSameDim | LookupMissingNoDim


def build_key(n_points: int, n_dims: int) -> str:
    return f"dd{n_dims}_nn{n_points}"


def load_db(path: Path = LHS_DB_PATH) -> dict:
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"LHS database pickle not found at {path}. "
            f"Set LHS_DB_PATH in scripts/query_lhs.py to the correct location."
        ) from e


def _parse_key(key: str) -> Optional[tuple[int, int]]:
    m = _KEY_RE.match(key)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))  # (n_dims, n_points)


def available_dims(db: dict) -> list[int]:
    dims: set[int] = set()
    for k in db.keys():
        parsed = _parse_key(k)
        if parsed is not None:
            dims.add(parsed[0])
    return sorted(dims)


def available_points_at_dim(db: dict, n_dims: int) -> list[int]:
    points: list[int] = []
    for k in db.keys():
        parsed = _parse_key(k)
        if parsed is not None and parsed[0] == n_dims:
            points.append(parsed[1])
    return sorted(points)


def nearest_n_points(candidates: list[int], target: int, k: int = 3) -> list[int]:
    ordered = sorted(candidates, key=lambda c: (abs(c - target), c))
    return ordered[:k]


def lookup(n_points: int, n_dims: int, db: Optional[dict] = None) -> LookupResult:
    if not isinstance(n_points, int) or isinstance(n_points, bool) or n_points <= 0:
        raise ValueError(f"n_points must be a positive int, got {n_points!r}")
    if not isinstance(n_dims, int) or isinstance(n_dims, bool) or n_dims <= 0:
        raise ValueError(f"n_dims must be a positive int, got {n_dims!r}")

    if db is None:
        db = load_db()

    key = build_key(n_points, n_dims)
    if key in db:
        arr = db[key]
        return LookupSuccess(key=key, shape=tuple(arr.shape), array=arr)

    points_at_dim = available_points_at_dim(db, n_dims)
    if points_at_dim:
        return LookupMissingSameDim(
            key_attempted=key,
            n_dims=n_dims,
            requested_n_points=n_points,
            nearby=nearest_n_points(points_at_dim, n_points, k=3),
        )

    return LookupMissingNoDim(
        key_attempted=key,
        n_dims=n_dims,
        available_dims=available_dims(db),
    )


def _result_to_json(result: LookupResult) -> str:
    if isinstance(result, LookupSuccess):
        payload = {"kind": "success", "key": result.key, "shape": list(result.shape)}
    elif isinstance(result, LookupMissingSameDim):
        payload = {
            "kind": "missing_same_dim",
            "key_attempted": result.key_attempted,
            "n_dims": result.n_dims,
            "requested_n_points": result.requested_n_points,
            "nearby": result.nearby,
        }
    else:
        payload = {
            "kind": "missing_no_dim",
            "key_attempted": result.key_attempted,
            "n_dims": result.n_dims,
            "available_dims": result.available_dims,
        }
    return json.dumps(payload)


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Look up an LHS design.")
    p.add_argument("--n-points", type=int, required=True)
    p.add_argument("--n-dims", type=int, required=True)
    p.add_argument("--db-path", type=Path, default=LHS_DB_PATH)
    try:
        args = p.parse_args(argv)
    except SystemExit:
        return 2

    try:
        db = load_db(args.db_path)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 3

    try:
        result = lookup(args.n_points, args.n_dims, db=db)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2

    print(_result_to_json(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
