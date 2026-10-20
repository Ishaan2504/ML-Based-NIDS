"""Dataset discovery and schema reporting. This phase never guesses from absent data."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from nids.common.errors import DatasetMissingError, DatasetSchemaError, UnmappedLabelError
from nids.data.adapters import CicIds2017Adapter
from nids.data.loader import (
    detect_variant,
    load_forbidden_features,
    load_label_map,
    load_raw_file,
    normalize_label,
)


def _column_statistics(frame: pd.DataFrame) -> dict[str, dict[str, object]]:
    report: dict[str, dict[str, object]] = {}
    for name in frame.columns:
        if name in {"source_file", "row_in_file"}:
            continue
        values = frame[name]
        numeric = pd.to_numeric(values, errors="coerce")
        report[name] = {
            "dtype": str(values.dtype),
            "missing_count": int(values.isna().sum()),
            "positive_infinity_count": int(np.isposinf(numeric).sum()),
            "negative_infinity_count": int(np.isneginf(numeric).sum()),
            "negative_count": int((numeric < 0).sum()),
            "non_numeric_count": int((values.notna() & numeric.isna()).sum()),
            "unique_count": int(values.nunique(dropna=True)),
            "constant": bool(values.nunique(dropna=True) <= 1),
        }
    return report


def validate_dataset(
    raw_dir: str | Path = "data/raw/cicids2017",
    reports_dir: str | Path = "reports",
) -> dict[str, object]:
    """Inspect each CSV and write JSON/Markdown schema reports."""
    adapter = CicIds2017Adapter(raw_dir)
    files = adapter.list_files()
    if not files:
        raise DatasetMissingError(
            "No CIC-IDS2017 CSV files found in data/raw/cicids2017/. "
            "Place the manually acquired CSV files there, then run "
            "python scripts/run_pipeline.py --stage validate."
        )

    label_map = load_label_map()
    forbidden = load_forbidden_features()
    file_reports: list[dict[str, object]] = []
    column_sets: dict[str, set[str]] = {}
    numeric_sets: dict[str, set[str]] = {}
    variants: dict[str, str] = {}
    label_counts: dict[str, int] = {}
    family_counts: dict[str, int] = {}
    total_rows = 0
    for path in files:
        frame = load_raw_file(path)
        variants[path.name] = detect_variant(frame.columns)
        column_sets[path.name] = set(frame.columns) - {"source_file", "row_in_file"}
        numeric_sets[path.name] = {
            name
            for name in column_sets[path.name]
            if name != "Label"
            and "__dup" not in name
            and "__duplicate_identical_" not in name
            and pd.to_numeric(frame[name], errors="coerce").notna().any()
        }
        if "Label" not in frame:
            raise DatasetSchemaError(f"Required Label column missing from {path.name}")
        raw_labels = frame["Label"].dropna().astype(str)
        normalized = raw_labels.map(normalize_label)
        valid_labels = normalized[raw_labels.str.strip().ne("") & normalized.ne("label")]
        unmapped = sorted(set(valid_labels) - set(label_map))
        if unmapped:
            originals = sorted(set(raw_labels[normalized.isin(unmapped)]))
            raise UnmappedLabelError(originals)
        counts = raw_labels[raw_labels.str.strip().ne("") & normalized.ne("label")].value_counts()
        for raw_label, count in counts.items():
            key = str(raw_label)
            label_counts[key] = label_counts.get(key, 0) + int(count)
            family = str(label_map[normalize_label(key)]["family"])
            family_counts[family] = family_counts.get(family, 0) + int(count)
        total_rows += len(frame)
        file_reports.append(
            {
                "file": path.name,
                "rows": len(frame),
                "encoding": frame.attrs.get("encoding"),
                "variant": variants[path.name],
                "columns": _column_statistics(frame),
                "normalized_columns": sorted(column_sets[path.name]),
                "duplicate_columns": frame.attrs.get("duplicate_columns", []),
            }
        )

    if len(set(variants.values())) > 1:
        raise DatasetSchemaError(f"Mixed CIC-IDS2017 variants found: {variants}")
    union = set.union(*column_sets.values())
    intersection = set.intersection(*column_sets.values())
    consistency = len(intersection) / len(union) if union else 0.0
    if consistency < 0.90:
        raise DatasetSchemaError(
            f"Fewer than 90% of expected columns are shared across files "
            f"({consistency:.1%}); inspect reports/schema_report.json."
        )
    eligible = sorted(set.intersection(*numeric_sets.values()) - forbidden)
    if not eligible:
        raise DatasetSchemaError("No numeric feature columns remain in the dataset.")
    report: dict[str, object] = {
        "dataset": "CIC-IDS2017",
        "files": file_reports,
        "detected_variant": next(iter(set(variants.values()))),
        "total_rows_before_cleaning": total_rows,
        "cross_file_consistency": {
            "shared_column_fraction": consistency,
            "intersection": sorted(intersection),
            "dropped_columns": {name: sorted(cols - intersection) for name, cols in column_sets.items()},
        },
        "labels": {"raw_counts": label_counts, "family_counts": family_counts},
        "feature_column_count": len(eligible),
    }
    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)
    (reports_path / "schema_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    lines = [
        "# CIC-IDS2017 schema report",
        "",
        f"- Variant: {report['detected_variant']}",
        f"- Files: {len(file_reports)}",
        f"- Rows before cleaning: {total_rows}",
        f"- Shared column fraction: {consistency:.1%}",
        f"- Eligible feature columns: {len(eligible)}",
        "",
        "## Files",
        "",
        "| File | Rows | Encoding | Variant |",
        "|---|---:|---|---|",
    ]
    lines.extend(
        f"| {item['file']} | {item['rows']} | {item['encoding']} | {item['variant']} |"
        for item in file_reports
    )
    (reports_path / "schema_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report
