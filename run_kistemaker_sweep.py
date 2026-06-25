import csv
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

from kistemaker import run_kistemaker  # adjust import to wherever run_kistemaker lives

PARAM_NAMES = [
    "triceps_long_head",
    "triceps_lateral_head",
    "triceps_medial_head",
    "anconeus",
    "supinator",
    "biceps_long_head",
    "biceps_short_head",
    "brachialis",
    "brachioradialis",
]


def load_points(csv_path):
    points = []
    with open(csv_path, newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    rows = rows[1:] if rows and not _is_numeric_row(rows[0]) else rows
    for row in rows:
        values = [float(v) for v in row]
        points.append(dict(zip(PARAM_NAMES, values)))
    return points


def _is_numeric_row(row):
    try:
        [float(v) for v in row]
        return True
    except ValueError:
        return False


def run_one(params):
    return params, run_kistemaker(**params)


def main(csv_path, n_workers=4):
    points = load_points(csv_path)
    results = []
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = [executor.submit(run_one, params) for params in points]
        for future in as_completed(futures):
            params, final_elbow_angle = future.result()
            results.append((params, final_elbow_angle))
    return results


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "lhs_dd9_nn100.csv"
    n_workers = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    results = main(csv_path, n_workers)
    for params, angle in results:
        print(params, "->", angle)
