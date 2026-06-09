"""
convert_csv.py — Render a saved LHS CSV as a code snippet string.

Deterministic (D) step. Returns a *string* containing source code that, if
pasted into a Python REPL, reconstructs the design as a numpy array, a pandas
DataFrame, or a torch tensor. This module does NOT import numpy / pandas /
torch and does NOT produce real array objects — the rendering is text only,
so the skill can run on stdlib Python.

Contract: see ../README.md sections 3.1, 5; SKILL.md "Followup turns".
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Literal, Optional


Format = Literal["numpy", "pandas", "pytorch"]

_VALID_FORMATS = ("numpy", "pandas", "pytorch")


def _read_csv(csv_path: Path) -> list[list[float]]:
    with open(csv_path, "r", newline="") as f:
        reader = csv.reader(f)
        rows = [[float(v) for v in row] for row in reader if row]
    return rows


def _format_rows(rows: list[list[float]]) -> str:
    inner = ",\n    ".join(
        "[" + ", ".join(repr(v) for v in row) + "]" for row in rows
    )
    return f"[\n    {inner}\n]"


def convert(csv_path: Path, fmt: Format) -> str:
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    if fmt not in _VALID_FORMATS:
        raise ValueError(
            f"Unsupported format {fmt!r}. Supported: {_VALID_FORMATS}"
        )

    rows = _read_csv(csv_path)
    n_cols = len(rows[0]) if rows else 0
    body = _format_rows(rows)

    if fmt == "numpy":
        return f"x = np.array({body})"

    if fmt == "pandas":
        columns = [f"x{i + 1}" for i in range(n_cols)]
        return f"x = pd.DataFrame({body}, columns={columns!r})"

    return f"x = torch.tensor({body}, dtype=torch.float32)"


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Render an LHS CSV as a code snippet.")
    p.add_argument("--csv-path", type=Path, required=True)
    p.add_argument("--format", choices=list(_VALID_FORMATS), required=True)
    try:
        args = p.parse_args(argv)
    except SystemExit:
        return 2

    try:
        out = convert(args.csv_path, args.format)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 5

    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
