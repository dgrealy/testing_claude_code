"""
query_lhs.py — Look up a Latin hypercube design in the pickle database.

This is a deterministic (D) step. The model never invokes the lookup logic
directly — it calls this script with parsed integer params. All numeric and
key-handling logic lives here.

Contract: see ../README.md sections 3, 4, 5.

Implementation status: STUB. Fill in the TODOs.
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# TODO: Set this to the actual pickle path on the user's system.
# Hardcoded by design — see README section 8. Configurable by editing this
# constant, not by runtime input.
LHS_DB_PATH: Path = Path("/path/to/lhs_database.p")


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class LookupSuccess:
    """The requested design was found in the database."""
    key: str
    shape: tuple[int, int]
    # The ndarray itself is not serialized to JSON; the caller reads it
    # from this object directly when invoking as a library, or reads
    # it from the CSV that save_csv.py writes.

    kind: str = "success"


@dataclass
class LookupMissingSameDim:
    """No design at the requested (n_points, n_dims), but the n_dims exists.

    `nearby` is the closest 3 n_points values at the same n_dims, sorted by
    absolute distance to the requested n_points (ties broken by smaller value
    first).
    """
    key_attempted: str
    n_dims: int
    requested_n_points: int
    nearby: list[int]
    kind: str = "missing_same_dim"


@dataclass
class LookupMissingNoDim:
    """No designs exist at the requested n_dims at all."""
    key_attempted: str
    n_dims: int
    available_dims: list[int]  # All n_dims values that DO exist in the DB.
    kind: str = "missing_no_dim"


LookupResult = LookupSuccess | LookupMissingSameDim | LookupMissingNoDim


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_key(n_points: int, n_dims: int) -> str:
    """Return the database key for the given (n_points, n_dims).

    Format: 'dd<n_dims>_nn<n_points>'. Example: build_key(40, 3) == 'dd3_nn40'.

    >>> build_key(40, 3)
    'dd3_nn40'
    >>> build_key(20, 2)
    'dd2_nn20'
    """
    # TODO: implement. One-liner.
    raise NotImplementedError


def load_db(path: Path = LHS_DB_PATH) -> dict:
    """Load the pickle database.

    Returns the dict directly. Each value is expected to be a numpy ndarray
    of shape (n_points, n_dims) where n_points and n_dims are derivable from
    the key.

    Raises FileNotFoundError if the path doesn't exist (with a helpful message
    pointing at LHS_DB_PATH).
    """
    # TODO: implement. Open with pickle.load. On FileNotFoundError, raise with
    # a message that names LHS_DB_PATH and tells the developer to set it.
    raise NotImplementedError


def available_dims(db: dict) -> list[int]:
    """Return the sorted list of n_dims values present in the DB.

    Parses each key of the form 'dd<D>_nn<N>' to extract D. Returns a sorted
    deduplicated list.
    """
    # TODO: implement. Use a regex or split on '_' to extract dims.
    raise NotImplementedError


def available_points_at_dim(db: dict, n_dims: int) -> list[int]:
    """Return the sorted list of n_points values present in the DB at n_dims.

    Empty list if no designs exist at this n_dims.
    """
    # TODO: implement.
    raise NotImplementedError


def nearest_n_points(candidates: list[int], target: int, k: int = 3) -> list[int]:
    """Return the k values from `candidates` closest to `target`.

    Sorted by absolute distance to target ascending; ties broken by smaller
    value first.

    >>> nearest_n_points([40, 50, 100], 75)
    [50, 100, 40]
    >>> nearest_n_points([40, 50, 100], 50)
    [50, 40, 100]
    >>> nearest_n_points([40], 75)
    [40]
    """
    # TODO: implement.
    raise NotImplementedError


def lookup(n_points: int, n_dims: int, db: Optional[dict] = None) -> LookupResult:
    """Look up a design. Returns one of the three LookupResult variants.

    Args:
        n_points: requested number of points (must be a positive int).
        n_dims: requested number of dimensions (must be a positive int).
        db: optional pre-loaded DB dict (for tests). If None, loads from
            LHS_DB_PATH.

    Returns:
        LookupSuccess if the key is present.
        LookupMissingSameDim if n_dims exists but n_points doesn't at that dim.
        LookupMissingNoDim if n_dims is not in the DB at all.

    Raises:
        ValueError if n_points or n_dims is not a positive int.
        FileNotFoundError if the DB pickle is missing.
    """
    # TODO: implement.
    # 1. Validate inputs (positive ints).
    # 2. Load DB if not provided.
    # 3. Build key. If key in db: return LookupSuccess with shape from the array.
    # 4. Else check available_points_at_dim(db, n_dims). If non-empty:
    #    return LookupMissingSameDim with nearest_n_points(..., k=3).
    # 5. Else: return LookupMissingNoDim with available_dims(db).
    raise NotImplementedError


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point. Prints a JSON result to stdout.

    Usage: python query_lhs.py --n-points 40 --n-dims 3

    Output (success):
        {"kind": "success", "key": "dd3_nn40", "shape": [40, 3]}

    Output (missing, same dim):
        {"kind": "missing_same_dim", "key_attempted": "dd3_nn75",
         "n_dims": 3, "requested_n_points": 75, "nearby": [50, 100, 40]}

    Output (missing, no dim):
        {"kind": "missing_no_dim", "key_attempted": "dd11_nn40",
         "n_dims": 11, "available_dims": [2, 3, 4, 5, 7]}

    Exit codes:
        0 on success of any result kind (the kind disambiguates).
        2 on usage error.
        3 on DB-not-found.

    Note: this CLI returns metadata only. The actual ndarray is *not* printed
    to stdout — that's what save_csv.py is for. The skill calls query_lhs.py
    first to disambiguate availability, then save_csv.py with the same params
    if the result was a success.
    """
    # TODO: implement.
    # Argparse: --n-points (int, required), --n-dims (int, required),
    #          --db-path (path, optional, defaults to LHS_DB_PATH).
    # Call lookup(); serialize result via dataclasses.asdict; json.dumps to stdout.
    # Note: shape tuple must serialize as a list.
    raise NotImplementedError


if __name__ == "__main__":
    sys.exit(main())
