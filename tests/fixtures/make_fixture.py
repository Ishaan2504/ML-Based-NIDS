"""Generate small, explicitly synthetic CIC-shaped CSVs for tests only."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pandas as pd


def make_frame(rows: int = 3000, seed: int = 42) -> pd.DataFrame:
    """Return a deterministic variant-A frame with representative CSV defects."""
    rng = np.random.default_rng(seed)
    labels = np.resize(np.array(["BENIGN", "DoS Hulk", "PortScan"]), rows)
    attack = labels != "BENIGN"
    means = attack.astype(float)[:, None] * 2.0
    values = rng.normal(loc=means, scale=1.0, size=(rows, 20))
    frame = pd.DataFrame(values, columns=[f"fixture_feature_{i:02d}" for i in range(20)])
    frame.insert(0, "Label", labels)
    frame.insert(0, "Timestamp", "7/7/2017 9:00")
    frame.insert(0, "Destination IP", "192.0.2.2")
    frame.insert(0, "Destination Port", 80)
    frame.insert(0, "Source IP", "192.0.2.1")
    frame.insert(0, "Flow ID", [f"fixture-{i}" for i in range(rows)])
    frame.loc[0, "fixture_feature_00"] = np.inf
    frame.loc[1, "fixture_feature_01"] = np.nan
    frame.loc[2, "fixture_feature_02"] = -2.0
    frame.loc[3, "Label"] = "Web Attack \u2013 XSS"
    return frame


def write_fixture(path: str | Path, rows: int = 3000, seed: int = 42) -> Path:
    """Write an explicitly synthetic CSV with whitespace and duplicate headers."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = make_frame(rows, seed)
    columns = list(frame.columns)
    columns[0] = " Flow   ID "
    columns.append("fixture_feature_00")
    with path.open("w", encoding="cp1252", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        first_row = next(frame.itertuples(index=False, name=None))
        for row in frame.itertuples(index=False, name=None):
            writer.writerow([*row, float(row[6]) + 1.0])
        writer.writerow([*first_row, float(first_row[6]) + 1.0])
        # The CSV defects are test data and must never be used for model reporting.
        writer.writerow(columns)
        writer.writerow(["", "", "", "", "", "", "", *([""] * 20)])
    return path
