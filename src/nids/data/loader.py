"""CSV loading and canonical column/label normalization."""

from __future__ import annotations

import csv
import re
from pathlib import Path

import pandas as pd
import yaml

from nids.common.errors import EmptyFileError

ENCODINGS = ("utf-8", "cp1252", "latin-1")
_ROOT = Path(__file__).resolve().parents[3]


def normalize_column_name(name: object) -> str:
    """Strip a name and collapse runs of whitespace without changing punctuation."""
    return re.sub(r"\s+", " ", str(name).strip())


def normalize_label(label: object) -> str:
    """Normalize label spelling according to the technical specification."""
    value = str(label).strip()
    value = re.sub(r"[^\x00-\x7f]+", "-", value)
    value = re.sub(r"\s+", " ", value).strip(" -")
    return value.casefold()


def load_column_aliases(path: str | Path | None = None) -> dict[str, list[str]]:
    config_path = Path(path) if path else _ROOT / "config" / "columns.yaml"
    with config_path.open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream) or {}
    aliases = config.get("metadata_aliases", {})
    return {
        canonical: [normalize_column_name(canonical), *(normalize_column_name(a) for a in values)]
        for canonical, values in aliases.items()
    }


def load_forbidden_features(path: str | Path | None = None) -> set[str]:
    config_path = Path(path) if path else _ROOT / "config" / "columns.yaml"
    with config_path.open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream) or {}
    return set(config.get("forbidden_features", []))


def load_label_map(path: str | Path | None = None) -> dict[str, dict[str, object]]:
    config_path = Path(path) if path else _ROOT / "config" / "label_map.yaml"
    with config_path.open(encoding="utf-8") as stream:
        labels = (yaml.safe_load(stream) or {}).get("labels", {})
    return {normalize_label(label): value for label, value in labels.items()}


def canonicalize_columns(columns: list[object]) -> list[str]:
    aliases = load_column_aliases()
    reverse = {
        alias.casefold(): canonical
        for canonical, names in aliases.items()
        for alias in names
    }
    return [reverse.get(normalize_column_name(name).casefold(), normalize_column_name(name)) for name in columns]


def _read_with_encoding(path: Path) -> tuple[list[str], pd.DataFrame, str]:
    errors: list[str] = []
    for encoding in ENCODINGS:
        try:
            with path.open("r", encoding=encoding, newline="") as stream:
                header = next(csv.reader(stream), None)
            if not header:
                raise EmptyFileError(f"CSV file has no header: {path}")
            # Reading columns by position preserves duplicate CSV headers for our own policy.
            frame = pd.read_csv(
                path,
                encoding=encoding,
                header=None,
                skiprows=1,
                names=list(range(len(header))),
                skip_blank_lines=False,
                low_memory=False,
            )
            return header, frame, encoding
        except EmptyFileError:
            raise
        except (UnicodeDecodeError, UnicodeError, csv.Error, pd.errors.ParserError) as exc:
            errors.append(f"{encoding}: {exc}")
    raise UnicodeError(f"Could not read {path} with supported encodings: {'; '.join(errors)}")


def load_raw_file(path: str | Path) -> pd.DataFrame:
    """Read a CSV, retain source row order, and resolve duplicate headers."""
    path = Path(path)
    header, frame, encoding = _read_with_encoding(path)
    if frame.empty:
        raise EmptyFileError(f"CSV file has a header but no data rows: {path}")

    names = canonicalize_columns(header)
    frame.columns = names
    duplicate_notes: list[dict[str, str]] = []
    output: list[str] = []
    seen: dict[str, int] = {}
    drop: list[str] = []
    for name in names:
        seen[name] = seen.get(name, 0) + 1
        if seen[name] == 1:
            output.append(name)
            continue
        prior_position = next(i for i, prior in enumerate(names[: len(output)]) if prior == name)
        prior = frame.iloc[:, prior_position]
        current_position = len(output)
        current = frame.iloc[:, current_position]
        if prior.equals(current):
            drop.append(current_position)
            output.append(f"{name}__duplicate_identical_{seen[name]}")
        else:
            renamed = f"{name}__dup{seen[name]}"
            duplicate_notes.append({"column": name, "renamed_to": renamed})
            output.append(renamed)

    if drop:
        frame = frame.drop(columns=drop)
        output = [name for i, name in enumerate(output) if i not in drop]
    frame.columns = output
    frame.insert(0, "source_file", path.name)
    frame.insert(1, "row_in_file", range(len(frame)))
    frame.attrs["encoding"] = encoding
    frame.attrs["duplicate_columns"] = duplicate_notes
    return frame


def detect_variant(columns: list[str] | pd.Index) -> str:
    names = {normalize_column_name(name).casefold() for name in columns}
    has_source = any(name in names for name in ("source ip", "src ip", "src_ip"))
    has_timestamp = any(name in names for name in ("timestamp", "time", "date time"))
    return "A" if has_source and has_timestamp else "B"
