"""
save_csv.py — Save a Latin hypercube design as a CSV file.

Deterministic (D) step. Writes /mnt/user-data/outputs/lhs_dd<D>_nn<N>.csv
using the stdlib csv module — no numpy, pandas, or torch. The array comes
from query_lhs.lookup() already normalized and as list-of-lists.

Contract: see ../README.md sections 3.1, 5.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Optional

import query_lhs
from query_lhs import LookupSuccess, build_key


OUTPUT_DIR: Path = Path("/mnt/user-data/outputs")


def output_path_for(n_points: int, n_dims: int, base_dir: Path = OUTPUT_DIR) -> Path:
    return base_dir / f"lhs_{build_key(n_points, n_dims)}.csv"


def _write_csv(path: Path, rows: list[list[float]]) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow([f"{v:.18e}" for v in row])


def save(n_points: int, n_dims: int, base_dir: Path = OUTPUT_DIR,
         db_path: Optional[Path] = None) -> Path:
    db = query_lhs.load_db(db_path) if db_path is not None else query_lhs.load_db()
    result = query_lhs.lookup(n_points, n_dims, db=db)
    if not isinstance(result, LookupSuccess):
        raise KeyError(repr(result))

    base_dir.mkdir(parents=True, exist_ok=True)
    path = output_path_for(n_points, n_dims, base_dir)
    _write_csv(path, result.array)
    return path


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Save an LHS design as CSV.")
    p.add_argument("--n-points", type=int, required=True)
    p.add_argument("--n-dims", type=int, required=True)
    p.add_argument("--base-dir", type=Path, default=OUTPUT_DIR)
    p.add_argument("--db-path", type=Path, default=None)
    try:
        args = p.parse_args(argv)
    except SystemExit:
        return 2

    try:
        path = save(args.n_points, args.n_dims, base_dir=args.base_dir,
                    db_path=args.db_path)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 4
    except KeyError as e:
        print(f"key not in DB: {e}", file=sys.stderr)
        return 3

    print(str(path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
