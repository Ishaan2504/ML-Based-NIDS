"""Domain errors raised by the NIDS data pipeline."""


class NIDSError(Exception):
    """Base class for expected pipeline failures."""


class DatasetMissingError(NIDSError):
    """Raised when no user supplied CIC-IDS2017 CSV files are present."""


class EmptyFileError(NIDSError):
    """Raised when a CSV contains a header but no data rows."""


class DatasetSchemaError(NIDSError):
    """Raised when a dataset does not satisfy the required schema contract."""


class UnmappedLabelError(NIDSError):
    """Raised for labels that are not explicitly described in label_map.yaml."""

    def __init__(self, labels: list[str]):
        self.labels = sorted(set(labels))
        super().__init__(f"Unmapped labels found: {', '.join(self.labels)}")
