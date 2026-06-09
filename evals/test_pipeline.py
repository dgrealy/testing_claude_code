"""
test_pipeline.py — Unit tests for the deterministic scripts.

Covers the D layer in isolation: build_key, lookup (with normalization),
nearest_n_points, output_path_for, save, convert. Pure stdlib — no numpy /
pandas / torch imports.
"""

from __future__ import annotations

import csv
import pickle
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import query_lhs  # noqa: E402
import save_csv   # noqa: E402
import convert_csv  # noqa: E402


FIXTURE_DB = Path(__file__).parent / "fixtures" / "mini_lhs.p"


@pytest.fixture
def db() -> dict:
    with open(FIXTURE_DB, "rb") as f:
        return pickle.load(f)


class TestBuildKey:
    def test_basic(self):
        assert query_lhs.build_key(40, 3) == "dd3_nn40"

    def test_single_digit(self):
        assert query_lhs.build_key(20, 2) == "dd2_nn20"

    def test_large(self):
        assert query_lhs.build_key(1000, 10) == "dd10_nn1000"


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
        assert query_lhs.nearest_n_points([50, 90], 70)[0] == 50


class TestNormalize:
    def test_min_max_columnwise(self):
        rows = [[0.0, 10.0], [5.0, 20.0], [10.0, 30.0]]
        out = query_lhs.normalize(rows)
        assert out == [[0.0, 0.0], [0.5, 0.5], [1.0, 1.0]]

    def test_constant_column_is_zero(self):
        rows = [[7.0, 0.0], [7.0, 1.0]]
        out = query_lhs.normalize(rows)
        assert out[0][0] == 0.0
        assert out[1][0] == 0.0

    def test_empty(self):
        assert query_lhs.normalize([]) == []


class TestLookup:
    def test_success_shape(self, db):
        result = query_lhs.lookup(40, 3, db=db)
        assert isinstance(result, query_lhs.LookupSuccess)
        assert result.key == "dd3_nn40"
        assert result.shape == (40, 3)
        assert len(result.array) == 40
        assert len(result.array[0]) == 3

    def test_success_is_normalized(self, db):
        result = query_lhs.lookup(40, 3, db=db)
        cols = list(zip(*result.array))
        for c in cols:
            assert min(c) == pytest.approx(0.0)
            assert max(c) == pytest.approx(1.0)

    def test_missing_same_dim(self, db):
        result = query_lhs.lookup(75, 3, db=db)
        assert isinstance(result, query_lhs.LookupMissingSameDim)
        assert result.key_attempted == "dd3_nn75"
        assert result.nearby == [50, 100, 40]

    def test_missing_no_dim(self, db):
        result = query_lhs.lookup(40, 11, db=db)
        assert isinstance(result, query_lhs.LookupMissingNoDim)
        assert result.key_attempted == "dd11_nn40"
        assert 11 not in result.available_dims
        assert 3 in result.available_dims

    def test_negative_raises(self, db):
        with pytest.raises(ValueError):
            query_lhs.lookup(-1, 3, db=db)

    def test_zero_raises(self, db):
        with pytest.raises(ValueError):
            query_lhs.lookup(0, 3, db=db)


class TestSaveCSV:
    def test_writes_file(self, db, tmp_path, monkeypatch):
        monkeypatch.setattr(query_lhs, "load_db", lambda path=None: db)
        path = save_csv.save(40, 3, base_dir=tmp_path)
        assert path.exists()
        assert path.name == "lhs_dd3_nn40.csv"

    def test_csv_shape(self, db, tmp_path, monkeypatch):
        monkeypatch.setattr(query_lhs, "load_db", lambda path=None: db)
        path = save_csv.save(40, 3, base_dir=tmp_path)
        with open(path) as f:
            rows = [r for r in csv.reader(f) if r]
        assert len(rows) == 40
        assert len(rows[0]) == 3

    def test_csv_values_normalized(self, db, tmp_path, monkeypatch):
        monkeypatch.setattr(query_lhs, "load_db", lambda path=None: db)
        path = save_csv.save(40, 3, base_dir=tmp_path)
        with open(path) as f:
            rows = [[float(v) for v in r] for r in csv.reader(f) if r]
        cols = list(zip(*rows))
        for c in cols:
            assert min(c) == pytest.approx(0.0)
            assert max(c) == pytest.approx(1.0)

    def test_missing_key_raises(self, db, tmp_path, monkeypatch):
        monkeypatch.setattr(query_lhs, "load_db", lambda path=None: db)
        with pytest.raises(KeyError):
            save_csv.save(75, 3, base_dir=tmp_path)

    def test_output_path_deterministic(self):
        p = save_csv.output_path_for(40, 3, Path("/tmp"))
        assert str(p) == "/tmp/lhs_dd3_nn40.csv"


class TestConvertCSV:
    @pytest.fixture
    def sample_csv(self, tmp_path):
        path = tmp_path / "sample.csv"
        rows = [[i + j * 0.1 for j in range(3)] for i in range(4)]
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            for r in rows:
                writer.writerow([f"{v:.18e}" for v in r])
        return path, rows

    def test_numpy_is_string_snippet(self, sample_csv):
        path, _ = sample_csv
        out = convert_csv.convert(path, "numpy")
        assert isinstance(out, str)
        assert out.startswith("x = np.array(")
        assert out.rstrip().endswith(")")

    def test_pandas_is_string_snippet(self, sample_csv):
        path, _ = sample_csv
        out = convert_csv.convert(path, "pandas")
        assert isinstance(out, str)
        assert out.startswith("x = pd.DataFrame(")
        assert "'x1'" in out and "'x2'" in out and "'x3'" in out

    def test_pytorch_is_string_snippet(self, sample_csv):
        path, _ = sample_csv
        out = convert_csv.convert(path, "pytorch")
        assert isinstance(out, str)
        assert out.startswith("x = torch.tensor(")
        assert "dtype=torch.float32" in out

    def test_invalid_format(self, sample_csv):
        path, _ = sample_csv
        with pytest.raises(ValueError):
            convert_csv.convert(path, "polars")  # type: ignore[arg-type]

    def test_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            convert_csv.convert(tmp_path / "nope.csv", "numpy")
