"""
test_pipeline.py — Unit tests for the deterministic scripts.

These tests cover the D layer in isolation: build_key, lookup, nearest_n_points,
output_path_for, save, convert. They do NOT test the parsing layer (that's
the L step; see run_eval.py).

Run: pytest evals/test_pipeline.py

These tests must run in under a few seconds. If they don't, the cause is a
real performance issue worth investigating — not normal.

Implementation status: STUB. Fill in TODOs after the scripts compile.
"""

from __future__ import annotations

import pickle
import sys
from pathlib import Path

import numpy as np
import pytest


# Ensure scripts/ is importable.
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import query_lhs  # noqa: E402
import save_csv   # noqa: E402
import convert_csv  # noqa: E402


FIXTURE_DB = Path(__file__).parent / "fixtures" / "mini_lhs.p"


@pytest.fixture
def db() -> dict:
    """Load the small test database. Each value is a deterministic ndarray
    of the correct shape, with reproducible (seeded) values."""
    # TODO: replace with pickle.load once the fixture is built.
    with open(FIXTURE_DB, "rb") as f:
        return pickle.load(f)


# ---------------------------------------------------------------------------
# build_key
# ---------------------------------------------------------------------------

class TestBuildKey:
    def test_basic(self):
        assert query_lhs.build_key(40, 3) == "dd3_nn40"

    def test_single_digit(self):
        assert query_lhs.build_key(20, 2) == "dd2_nn20"

    def test_large(self):
        assert query_lhs.build_key(1000, 10) == "dd10_nn1000"


# ---------------------------------------------------------------------------
# nearest_n_points
# ---------------------------------------------------------------------------

class TestNearestNPoints:
    def test_three_candidates(self):
        assert query_lhs.nearest_n_points([40, 50, 100], 75) == [50, 100, 40]

    def test_exact_match_first(self):
        assert query_lhs.nearest_n_points([40, 50, 100], 50)[0] == 50

    def test_fewer_than_k(self):
        assert query_lhs.nearest_n_points([40], 75) == [40]

    def test_empty(self):
        assert query_lhs.nearest_n_points([], 75) == []

    def test_tie_smaller_wins(self):
        # 50 and 90 are both distance 20 from 70; 50 should come first.
        assert query_lhs.nearest_n_points([50, 90], 70)[0] == 50


# ---------------------------------------------------------------------------
# lookup
# ---------------------------------------------------------------------------

class TestLookup:
    def test_success(self, db):
        result = query_lhs.lookup(40, 3, db=db)
        assert isinstance(result, query_lhs.LookupSuccess)
        assert result.key == "dd3_nn40"
        assert result.shape == (40, 3)

    def test_missing_same_dim(self, db):
        # 75 points at 3 dims doesn't exist; 40, 50, 100 do.
        result = query_lhs.lookup(75, 3, db=db)
        assert isinstance(result, query_lhs.LookupMissingSameDim)
        assert result.key_attempted == "dd3_nn75"
        assert result.nearby == [50, 100, 40]

    def test_missing_no_dim(self, db):
        # 11 dims is not present in fixture.
        result = query_lhs.lookup(40, 11, db=db)
        assert isinstance(result, query_lhs.LookupMissingNoDim)
        assert result.key_attempted == "dd11_nn40"
        assert 11 not in result.available_dims
        assert 3 in result.available_dims  # sanity

    def test_negative_raises(self, db):
        with pytest.raises(ValueError):
            query_lhs.lookup(-1, 3, db=db)

    def test_zero_raises(self, db):
        with pytest.raises(ValueError):
            query_lhs.lookup(0, 3, db=db)


# ---------------------------------------------------------------------------
# save_csv
# ---------------------------------------------------------------------------

class TestSaveCSV:
    def test_writes_file(self, db, tmp_path, monkeypatch):
        # Patch the DB loader to return the fixture instead of reading
        # LHS_DB_PATH.
        monkeypatch.setattr(query_lhs, "load_db", lambda path=None: db)
        path = save_csv.save(40, 3, base_dir=tmp_path)
        assert path.exists()
        assert path.name == "lhs_dd3_nn40.csv"

    def test_csv_shape(self, db, tmp_path, monkeypatch):
        monkeypatch.setattr(query_lhs, "load_db", lambda path=None: db)
        path = save_csv.save(40, 3, base_dir=tmp_path)
        arr = np.loadtxt(path, delimiter=",")
        assert arr.shape == (40, 3)

    def test_missing_key_raises(self, db, tmp_path, monkeypatch):
        monkeypatch.setattr(query_lhs, "load_db", lambda path=None: db)
        with pytest.raises(KeyError):
            save_csv.save(75, 3, base_dir=tmp_path)

    def test_output_path_deterministic(self):
        p = save_csv.output_path_for(40, 3, Path("/tmp"))
        assert str(p) == "/tmp/lhs_dd3_nn40.csv"


# ---------------------------------------------------------------------------
# convert_csv
# ---------------------------------------------------------------------------

class TestConvertCSV:
    @pytest.fixture
    def sample_csv(self, tmp_path):
        path = tmp_path / "sample.csv"
        arr = np.arange(12, dtype=np.float64).reshape(4, 3)
        np.savetxt(path, arr, delimiter=",", fmt="%.18e")
        return path, arr

    def test_numpy(self, sample_csv):
        path, expected = sample_csv
        out = convert_csv.convert(path, "numpy")
        assert isinstance(out, np.ndarray)
        assert out.shape == (4, 3)
        np.testing.assert_allclose(out, expected)

    def test_pandas(self, sample_csv):
        pd = pytest.importorskip("pandas")
        path, expected = sample_csv
        out = convert_csv.convert(path, "pandas")
        assert isinstance(out, pd.DataFrame)
        assert list(out.columns) == ["x1", "x2", "x3"]
        assert out.shape == (4, 3)
        np.testing.assert_allclose(out.values, expected)

    def test_pytorch(self, sample_csv):
        torch = pytest.importorskip("torch")
        path, expected = sample_csv
        out = convert_csv.convert(path, "pytorch")
        assert isinstance(out, torch.Tensor)
        assert out.shape == (4, 3)
        assert out.dtype == torch.float32

    def test_invalid_format(self, sample_csv):
        path, _ = sample_csv
        with pytest.raises(ValueError):
            convert_csv.convert(path, "polars")  # type: ignore[arg-type]

    def test_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            convert_csv.convert(tmp_path / "nope.csv", "numpy")
