"""
convert_csv.py — Convert a saved LHS CSV to numpy, pandas, or pytorch.

This is a deterministic (D) step. Used both for explicit format requests and
for the followup conversion turn (user says "make it numpy" after a CSV
delivery).

Contract: see ../README.md sections 3.1, 5; SKILL.md "Followup turns".

Implementation status: STUB. Fill in the TODOs.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Literal, Optional


Format = Literal["numpy", "pandas", "pytorch"]


def convert(csv_path: Path, fmt: Format) -> Any:
    """Read the CSV and return it in the requested format.

    Args:
        csv_path: path to a CSV written by save_csv.py (no header, comma-sep).
        fmt: one of "numpy", "pandas", "pytorch".

    Returns:
        - "numpy" → numpy.ndarray of shape (N, D), dtype float64.
        - "pandas" → pandas.DataFrame of shape (N, D), columns ['x1', ..., 'xD'].
        - "pytorch" → torch.Tensor of shape (N, D), dtype torch.float32.

    Raises:
        FileNotFoundError: csv_path doesn't exist.
        ValueError: fmt is not one of the three supported values.
        ImportError: pandas or torch is requested but not installed (caller
            should surface this to the user; do NOT silently fall back).

    Notes:
        - Column names for pandas are 1-indexed: x1, x2, ..., xD. Match what
          a domain user would expect for a D-dimensional design.
        - pytorch dtype is float32 by convention for ML use; numpy stays
          float64 (the CSV is written at full float precision).
        - Do NOT do any data transformation (scaling, normalization). The
          design comes out exactly as it went in.
    """
    # TODO: implement.
    # if fmt == "numpy": return numpy.loadtxt(csv_path, delimiter=',')
    # if fmt == "pandas": load with numpy, wrap in DataFrame with x1..xD columns
    # if fmt == "pytorch": load with numpy, torch.from_numpy(...).float()
    # else: raise ValueError
    raise NotImplementedError


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point.

    Usage: python convert_csv.py --csv-path PATH --format {numpy,pandas,pytorch}

    Behavior:
        - "numpy": prints array via numpy.array_repr to stdout. (For the
          skill's purposes, the in-memory return value matters more than
          stdout — the model surfaces the array directly. CLI output is for
          debugging.)
        - "pandas": prints DataFrame.to_string() to stdout.
        - "pytorch": prints tensor repr to stdout.

    Exit codes: 0 on success, 2 on usage error, 5 on missing CSV.
    """
    # TODO: implement.
    raise NotImplementedError


if __name__ == "__main__":
    sys.exit(main())
