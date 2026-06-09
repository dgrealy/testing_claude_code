"""
build_fixture.py — Build the test fixture pickle `mini_lhs.p`.

The fixture mirrors the shape of the real LHS database (a dict mapping
keys like 'dd3_nn40' to lists-of-lists of the corresponding shape), with
reproducible seeded contents so tests are deterministic.

Run once: python evals/fixtures/build_fixture.py

The contents of each design are random-but-seeded, NOT real Latin hypercube
samples. The tests do not depend on the values being a valid LHS — only on
the shape and the lookup behavior.

This script is stdlib-only — no numpy import — to match the runtime skill's
dependency footprint.

Fixture contents (matches eval_cases.json _db_assumptions_for_tests):
    dd2_nn20, dd3_nn40, dd3_nn50, dd3_nn100, dd4_nn50, dd5_nn100, dd7_nn50
    Present n_dims: 2, 3, 4, 5, 7
    Absent n_dims: 1, 6, 8, 9, 10, 11+
"""

from __future__ import annotations

import pickle
import random
from pathlib import Path


FIXTURE_KEYS = [
    (2, 20),
    (3, 40),
    (3, 50),
    (3, 100),
    (4, 50),
    (5, 100),
    (7, 50),
]


def build() -> dict:
    rng = random.Random(20260526)
    db: dict[str, list[list[float]]] = {}
    for n_dims, n_points in FIXTURE_KEYS:
        key = f"dd{n_dims}_nn{n_points}"
        rows = [[rng.uniform(0.0, 1.0) for _ in range(n_dims)]
                for _ in range(n_points)]
        db[key] = rows
    return db


def main() -> None:
    out = Path(__file__).parent / "mini_lhs.p"
    db = build()
    with open(out, "wb") as f:
        pickle.dump(db, f)
    print(f"Wrote {out} with keys: {sorted(db.keys())}")


if __name__ == "__main__":
    main()
