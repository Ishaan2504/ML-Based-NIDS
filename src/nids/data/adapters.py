"""Dataset adapters keep source specific paths out of pipeline code."""

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd


class DatasetAdapter(ABC):
    """Interface implemented by supported flow datasets."""

    @abstractmethod
    def list_files(self) -> list[Path]:
        """Return the input files in deterministic order."""

    @abstractmethod
    def read_file(self, path: Path) -> pd.DataFrame:
        """Read and normalize one source file."""

    @abstractmethod
    def canonical_columns(self) -> dict[str, list[str]]:
        """Return canonical metadata names and their accepted aliases."""

    @abstractmethod
    def label_map(self) -> dict[str, dict[str, object]]:
        """Return the configured fine-label mapping."""


class CicIds2017Adapter(DatasetAdapter):
    """Adapter for manually acquired CIC-IDS2017 CSV files."""

    def __init__(self, raw_dir: str | Path = "data/raw/cicids2017") -> None:
        self.raw_dir = Path(raw_dir)

    def list_files(self) -> list[Path]:
        return sorted(path for path in self.raw_dir.glob("*.csv") if path.is_file())

    def read_file(self, path: Path) -> pd.DataFrame:
        from nids.data.loader import load_raw_file

        return load_raw_file(path)

    def canonical_columns(self) -> dict[str, list[str]]:
        from nids.data.loader import load_column_aliases

        return load_column_aliases()

    def label_map(self) -> dict[str, dict[str, object]]:
        from nids.data.loader import load_label_map

        return load_label_map()
