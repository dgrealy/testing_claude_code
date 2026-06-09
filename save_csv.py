"""
save_csv.py — Save a Latin hypercube design as a CSV file.

This is a deterministic (D) step. It produces the user-facing CSV deliverable
in /mnt/user-data/outputs/ with a predictable filename based on the DB key.

Contract: see ../README.md sections 3.1, 5.

Implementation status: STUB. Fill in the TODOs.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional


OUTPUT_DIR: Path = Path("/mnt/user-data/outputs")


def output_path_for(n_points: int, n_dims: int, base_dir: Path = OUTPUT_DIR) -> Path:
    """Return the deterministic output path for a given design.

    Format: <base_dir>/lhs_dd<n_dims>_nn<n_points>.csv

    >>> str(output_path_for(40, 3, Path("/tmp")))
    '/tmp/lhs_dd3_nn40.csv'
    """
    # TODO: implement.
    raise NotImplementedError


def save(n_points: int, n_dims: int, base_dir: Path = OUTPUT_DIR,
         db_path: Optional[Path] = None) -> Path:
    """Look up the design and save it as CSV.

    Args:
        n_points, n_dims: identify the design.
        base_dir: where to write. Defaults to /mnt/user-data/outputs/.
        db_path: optional override of the pickle path (for tests).

    Returns:
        The Path to the written CSV.

    Behavior:
        - Calls query_lhs.lookup() to retrieve the ndarray.
        - If the lookup returns anything other than LookupSuccess, raises
          KeyError with the lookup result's repr. (The caller should have
          already checked availability before calling save() — this is a
          defensive check, not the user-facing path.)
        - Writes the array to output_path_for(n_points, n_dims, base_dir).
        - CSV format: no header, no index, comma-separated, full float
          precision (use numpy.savetxt with fmt='%.18e').
        - Creates base_dir if it doesn't exist.
        - Overwrites any existing file at the path without prompting.
          (The path is deterministic; same params == same file == idempotent.)

    Raises:
        KeyError: lookup did not return a success.
        FileNotFoundError: DB pickle missing.
    """
    # TODO: implement.
    # 1. from query_lhs import lookup, LookupSuccess  (relative import; see below)
    # 2. result = lookup(n_points, n_dims, db=None) or load_db(db_path) and pass through
    # 3. If not isinstance(result, LookupSuccess): raise KeyError(repr(result))
    # 4. base_dir.mkdir(parents=True, exist_ok=True)
    # 5. path = output_path_for(n_points, n_dims, base_dir)
    # 6. numpy.savetxt(path, array, delimiter=',', fmt='%.18e')
    # 7. return path
    raise NotImplementedError


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point. Prints the written path to stdout on success.

    Usage: python save_csv.py --n-points 40 --n-dims 3

    Output: /mnt/user-data/outputs/lhs_dd3_nn40.csv
    Exit code: 0 on success, 3 if key not in DB (caller should have checked),
               4 if DB pickle missing.
    """
    # TODO: implement.
    raise NotImplementedError


if __name__ == "__main__":
    sys.exit(main())
