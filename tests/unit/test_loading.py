from __future__ import annotations

import csv

import pytest

from nids.common.errors import DatasetMissingError, EmptyFileError
from nids.data.loader import load_raw_file, normalize_label
from nids.data.validate import validate_dataset
from tests.fixtures.make_fixture import write_fixture


def test_load_normalizes_headers_and_resolves_duplicate_columns(tmp_path):
    path = write_fixture(tmp_path / "synthetic.csv", rows=10)
    frame = load_raw_file(path)

    assert "Flow ID" in frame.columns
    assert "fixture_feature_00" in frame.columns
    assert "fixture_feature_00__dup2" in frame.columns
    assert frame.attrs["encoding"] == "cp1252"
    assert frame["row_in_file"].tolist() == list(range(len(frame)))


def test_load_cp1252_label_normalizes_non_ascii_dash(tmp_path):
    path = tmp_path / "label.csv"
    path.write_text("Label,feature\nWeb Attack \u2013 XSS,1\n", encoding="cp1252")

    frame = load_raw_file(path)

    assert frame.loc[0, "Label"] == "Web Attack \u2013 XSS"
    assert normalize_label(frame.loc[0, "Label"]) == "web attack - xss"


def test_header_only_file_raises_empty_file_error(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("Label,feature\n", encoding="utf-8")

    with pytest.raises(EmptyFileError):
        load_raw_file(path)


def test_validation_without_csv_stops_with_dataset_message(tmp_path):
    with pytest.raises(DatasetMissingError, match="No CIC-IDS2017 CSV files"):
        validate_dataset(tmp_path / "raw", tmp_path / "reports")


def test_fixture_has_duplicate_header_and_repeated_header(tmp_path):
    path = write_fixture(tmp_path / "synthetic.csv", rows=4)
    with path.open(encoding="cp1252", newline="") as stream:
        records = list(csv.reader(stream))
    assert records[0].count("fixture_feature_00") == 2
    assert records[-2] == records[0]
    assert all(value == "" for value in records[-1])
