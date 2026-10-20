"""Small trusted-bundle adapter used by the HTTP service.

Training and prediction must eventually share the same serialized sklearn
pipeline. This adapter only loads a bundle selected through models/ACTIVE and
verified by its adjacent SHA-256 file; it never accepts a request-supplied path.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from backend.schemas.flow import FlowValidationError

logger = logging.getLogger(__name__)
SUPPORTED_SCHEMA_VERSION = 1
DEPENDENCY_VERSIONS = ("scikit-learn", "xgboost", "numpy", "pandas")


class BundleError(RuntimeError):
    """Raised when the configured local model bundle is not safe to load."""


def _get(item: Any, name: str, default: Any = None) -> Any:
    return item.get(name, default) if isinstance(item, dict) else getattr(item, name, default)


def _normalized_name(name: str) -> str:
    return " ".join(str(name).strip().split())


def _installed_versions() -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for package in DEPENDENCY_VERSIONS:
        try:
            result[package] = version(package)
        except PackageNotFoundError:
            result[package] = None
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Predictor:
    def __init__(self, bundle: Any, model_id: str, meta: dict[str, Any], versions_mismatch: bool):
        self.bundle = bundle
        self.model_id = model_id
        self.meta = meta
        self.version_mismatch = versions_mismatch
        self.feature_names = list(_get(bundle, "feature_names", []))
        self.threshold = float(_get(bundle, "threshold", 0.5))
        if not self.feature_names:
            raise BundleError("The model bundle has no feature_names list.")
        if not np.isfinite(self.threshold):
            raise BundleError("The model bundle has a non-finite operating threshold.")
        self.feature_lookup = {_normalized_name(name): name for name in self.feature_names}
        if len(self.feature_lookup) != len(self.feature_names):
            raise BundleError("The model bundle contains colliding normalized feature names.")

    @classmethod
    def from_dir(cls, model_dir: str | Path) -> "Predictor":
        root = Path(model_dir).resolve()
        active_file = root / "ACTIVE"
        if not active_file.is_file():
            raise BundleError(f"No active model marker found at {active_file}.")
        model_id = active_file.read_text(encoding="utf-8").strip()
        if not model_id or Path(model_id).name != model_id:
            raise BundleError("models/ACTIVE must contain a single model directory name.")
        bundle_dir = (root / model_id).resolve()
        if bundle_dir.parent != root:
            raise BundleError("The active model path must remain inside MODEL_DIR.")
        bundle_path = bundle_dir / "bundle.joblib"
        checksum_path = bundle_dir / "bundle.sha256"
        meta_path = bundle_dir / "bundle_meta.json"
        for required in (bundle_path, checksum_path, meta_path):
            if not required.is_file():
                raise BundleError(f"Required model artifact is missing: {required.name}.")

        expected_hash = checksum_path.read_text(encoding="ascii").strip().split()[0].lower()
        actual_hash = _sha256(bundle_path)
        if not hmac_compare(expected_hash, actual_hash):
            raise BundleError("The model bundle SHA-256 does not match bundle.sha256.")

        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
            raise BundleError(
                f"Unsupported model schema_version: {meta.get('schema_version')!r}."
            )

        # joblib is pickle-based and can execute code during loading. Only this
        # verified, configured local artifact is eligible to be loaded.
        bundle = joblib.load(bundle_path)
        if _get(bundle, "schema_version") != SUPPORTED_SCHEMA_VERSION:
            raise BundleError("The serialized model bundle has an unsupported schema_version.")
        saved = _get(bundle, "library_versions", {}) or meta.get("library_versions", {}) or {}
        installed = _installed_versions()
        mismatches = {
            name: {"saved": saved.get(name), "installed": installed.get(name)}
            for name in DEPENDENCY_VERSIONS
            if saved.get(name) and installed.get(name) and saved.get(name) != installed.get(name)
        }
        if mismatches:
            logger.warning("Model/library version mismatch: %s", mismatches)
        return cls(bundle, model_id, meta, bool(mismatches))

    def info(self) -> dict[str, Any]:
        binary = _get(self.bundle, "binary_pipeline")
        model_name = self.meta.get("model_name") or type(binary).__name__
        family_classes = _get(self.bundle, "family_classes", []) or []
        created_at = _get(self.bundle, "created_at") or self.meta.get("created_at")
        return {
            "status": "active",
            "model_name": model_name,
            "model_id": self.model_id,
            "threshold": self.threshold,
            "threshold_policy": _get(self.bundle, "threshold_policy"),
            "score_type": _get(self.bundle, "score_type", "model_score"),
            "score_description": (
                "This model score ranks flows by how attack-like the model finds them; "
                "it is not the probability that an attack occurred."
            ),
            "feature_names": self.feature_names,
            "feature_count": len(self.feature_names),
            "supported_families": list(family_classes),
            "trained_timestamp": created_at,
            "version_mismatch": self.version_mismatch,
            "dataset_info": _get(self.bundle, "dataset_info", {}),
            "metrics_refs": _get(self.bundle, "metrics_refs", {}),
        }

    def _frame(self, flows: list[dict[str, Any]]) -> tuple[pd.DataFrame, list[str], list[int]]:
        normalized_rows: list[dict[str, Any]] = []
        ignored: set[str] = set()
        imputed_counts: list[int] = []
        for row_index, flow in enumerate(flows):
            normalized: dict[str, Any] = {}
            for key, value in flow.items():
                clean_key = _normalized_name(key)
                if clean_key in normalized:
                    raise FlowValidationError(
                        "duplicate_feature",
                        f"Feature names collide after normalization: {key!r}.",
                    )
                if clean_key not in self.feature_lookup:
                    ignored.add(clean_key)
                    continue
                if isinstance(value, bool) or (value is not None and not isinstance(value, (int, float))):
                    raise FlowValidationError(
                        "invalid_feature_value",
                        f"Feature {key!r} must be a JSON number or null.",
                    )
                normalized[self.feature_lookup[clean_key]] = value
            missing = [name for name in self.feature_names if name not in normalized]
            if missing:
                raise FlowValidationError(
                    "missing_features",
                    "Required model features are missing.",
                    {"missing_features": missing[:30], "missing_count": len(missing)},
                )
            imputed_counts.append(sum(value is None for value in normalized.values()))
            normalized_rows.append(normalized)
        frame = pd.DataFrame(normalized_rows, columns=self.feature_names)
        return frame, sorted(ignored), imputed_counts

    def predict_one(self, flow: dict[str, Any]) -> dict[str, Any]:
        return self.predict_many([flow])[0]

    def predict_many(self, flows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not flows:
            raise FlowValidationError("empty_input", "At least one flow is required.")
        frame, ignored_fields, imputed_counts = self._frame(flows)
        pipeline = _get(self.bundle, "binary_pipeline")
        if pipeline is None:
            raise BundleError("The active model bundle has no binary_pipeline.")
        score_type = _get(self.bundle, "score_type", "model_score")
        if hasattr(pipeline, "predict_proba"):
            scores = np.asarray(pipeline.predict_proba(frame))[:, 1]
        elif hasattr(pipeline, "score_samples"):
            scores = -np.asarray(pipeline.score_samples(frame)).reshape(-1)
            score_type = "anomaly_score"
        elif hasattr(pipeline, "decision_function"):
            scores = np.asarray(pipeline.decision_function(frame)).reshape(-1)
            score_type = score_type or "decision_score"
        else:
            raise BundleError("The binary pipeline exposes no supported scoring method.")

        decisions = scores >= self.threshold
        family_pipeline = _get(self.bundle, "multiclass_pipeline")
        families: list[Any] = [None] * len(flows)
        family_scores: list[Any] = [None] * len(flows)
        family_uncertain: list[bool | None] = [None] * len(flows)
        if family_pipeline is not None and decisions.any():
            selected = frame.loc[decisions]
            predicted = family_pipeline.predict(selected)
            label_encoder = _get(self.bundle, "label_encoder")
            if (
                label_encoder is not None
                and hasattr(label_encoder, "inverse_transform")
                and all(isinstance(value, (int, np.integer)) for value in predicted)
            ):
                predicted = label_encoder.inverse_transform(predicted)
            else:
                family_classes = list(_get(self.bundle, "family_classes", []))
                if family_classes and all(isinstance(value, (int, np.integer)) for value in predicted):
                    predicted = [family_classes[int(value)] for value in predicted]
            probabilities = (
                np.asarray(family_pipeline.predict_proba(selected))
                if hasattr(family_pipeline, "predict_proba")
                else None
            )
            positions = np.flatnonzero(decisions)
            for offset, position in enumerate(positions):
                families[position] = str(predicted[offset])
                if probabilities is not None:
                    family_scores[position] = float(probabilities[offset].max())
                    family_uncertain[position] = bool(probabilities[offset].max() < 0.5)
        severities = self._severity_levels(scores, decisions, families, family_uncertain)
        now = datetime.now(timezone.utc).isoformat()
        return [
            {
                "row_index": index,
                "score": float(scores[index]),
                "score_type": score_type,
                "threshold": self.threshold,
                "is_malicious_prediction": bool(decisions[index]),
                "attack_family": families[index],
                "family_score": family_scores[index],
                "family_uncertain": family_uncertain[index],
                "severity": severities[index],
                "imputed_feature_count": imputed_counts[index],
                "out_of_range_feature_count": self._out_of_range_count(frame.iloc[index]),
                "non_numeric_values": 0,
                "ignored_fields": ignored_fields,
                "model_id": self.model_id,
                "generated_at": now,
            }
            for index in range(len(flows))
        ]

    def _severity_levels(
        self,
        scores: np.ndarray,
        decisions: np.ndarray,
        families: list[Any],
        uncertain: list[bool | None],
    ) -> list[str | None]:
        config = _get(self.bundle, "severity_config", {}) or {}
        edges = _get(self.bundle, "score_tier_edges")
        impacts = config.get("family_impact") if isinstance(config, dict) else None
        if not isinstance(edges, (list, tuple)) or len(edges) != 2:
            return [None] * len(scores)
        if not isinstance(impacts, dict):
            return [None] * len(scores)
        low_edge, high_edge = float(edges[0]), float(edges[1])
        results: list[str | None] = []
        for score, is_malicious, family, is_uncertain in zip(scores, decisions, families, uncertain):
            if not is_malicious:
                results.append(None)
                continue
            family_key = "Unknown" if family is None or is_uncertain else str(family)
            impact = int(impacts.get(family_key, impacts.get("Unknown", 2)))
            tier = 1 if score < low_edge else 2 if score < high_edge else 3
            total = impact + tier
            results.append("Critical" if total >= 6 else "High" if total == 5 else "Medium" if total == 4 else "Low")
        return results

    def _out_of_range_count(self, row: pd.Series) -> int:
        ranges = _get(self.bundle, "feature_ranges", {}) or {}
        count = 0
        for feature, value in row.items():
            if pd.isna(value) or feature not in ranges:
                continue
            bounds = ranges[feature]
            try:
                if isinstance(bounds, dict):
                    minimum, maximum = bounds.get("min"), bounds.get("max")
                else:
                    minimum, maximum = bounds[0], bounds[1]
                count += int(value < minimum or value > maximum)
            except (TypeError, ValueError, IndexError):
                continue
        return count


def hmac_compare(left: str, right: str) -> bool:
    import hmac

    return hmac.compare_digest(left, right)
