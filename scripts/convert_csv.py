"""
convert_csv.py — Convert a saved LHS CSV to numpy, pandas, or pytorch.

Deterministic (D) step. No data transformation — the design comes out exactly
as it went in.

Contract: see ../README.md sections 3.1, 5; SKILL.md "Followup turns".
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Literal, Optional

import numpy as np


Format = Literal["numpy", "pandas", "pytorch"]

_VALID_FORMATS = ("numpy", "pandas", "pytorch")


def convert(csv_path: Path, fmt: Format) -> Any:
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    if fmt not in _VALID_FORMATS:
        raise ValueError(
            f"Unsupported format {fmt!r}. Supported: {_VALID_FORMATS}"
        )

    arr = np.loadtxt(csv_path, delimiter=",")
    if arr.ndim == 1:
        arr = arr.reshape(-1, 1)

    if fmt == "numpy":
        return arr

    if fmt == "pandas":
        import pandas as pd
        columns = [f"x{i + 1}" for i in range(arr.shape[1])]
        return pd.DataFrame(arr, columns=columns)

    import torch
    return torch.from_numpy(arr).float()


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Convert an LHS CSV to a tensor format.")
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

    if args.format == "numpy":
        print(np.array_repr(out))
    elif args.format == "pandas":
        print(out.to_string())
    else:
        print(repr(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
