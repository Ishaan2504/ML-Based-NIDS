"""Inference adapter for the NSL-KDD XGBoost model used by ML-Cyber-Threat-Detector."""

from __future__ import annotations

import hashlib
import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

KDD_COLUMNS = [
    "duration", "protocol_type", "service", "flag", "src_bytes", "dst_bytes",
    "land", "wrong_fragment", "urgent", "hot", "num_failed_logins", "logged_in",
    "num_compromised", "root_shell", "su_attempted", "num_root", "num_file_creations",
    "num_shells", "num_access_files", "num_outbound_cmds", "is_host_login",
    "is_guest_login", "count", "srv_count", "serror_rate", "srv_serror_rate",
    "rerror_rate", "srv_rerror_rate", "same_srv_rate", "diff_srv_rate",
    "srv_diff_host_rate", "dst_host_count", "dst_host_srv_count",
    "dst_host_same_srv_rate", "dst_host_diff_srv_rate", "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate", "dst_host_serror_rate", "dst_host_srv_serror_rate",
    "dst_host_rerror_rate", "dst_host_srv_rerror_rate", "label", "difficulty",
]
KDD_FEATURES = KDD_COLUMNS[:-2]
CATEGORICAL_FEATURES = ("protocol_type", "service", "flag")
ATTACK_CATEGORIES = {
    "normal": "Normal",
    "back": "DoS", "land": "DoS", "neptune": "DoS", "pod": "DoS", "smurf": "DoS",
    "teardrop": "DoS", "mailbomb": "DoS", "apache2": "DoS", "processtable": "DoS",
    "udpstorm": "DoS", "worm": "DoS",
    "ipsweep": "Probe", "nmap": "Probe", "portsweep": "Probe", "satan": "Probe",
    "mscan": "Probe", "saint": "Probe",
    "ftp_write": "R2L", "guess_passwd": "R2L", "imap": "R2L", "multihop": "R2L",
    "phf": "R2L", "spy": "R2L", "warezclient": "R2L", "warezmaster": "R2L",
    "sendmail": "R2L", "named": "R2L", "snmpgetattack": "R2L", "snmpguess": "R2L",
    "xlock": "R2L", "xsnoop": "R2L", "httptunnel": "R2L",
    "buffer_overflow": "U2R", "loadmodule": "U2R", "perl": "U2R", "rootkit": "U2R",
    "ps": "U2R", "sqlattack": "U2R", "xterm": "U2R",
}


class ModelLoadError(RuntimeError):
    """Raised when the configured NSL-KDD model artifact cannot be loaded."""


class NslKddPredictor:
    """Load and serve the trained XGBoost model with its original preprocessing."""

    def __init__(self, model_data: dict[str, Any], model_id: str):
        required = {"model", "label_encoders", "scaler", "feature_names", "reverse_label_mapping"}
        missing = sorted(required - model_data.keys())
        if missing:
            raise ModelLoadError(f"Model artifact is missing required entries: {', '.join(missing)}")

        self.model = model_data["model"]
        self.label_encoders = model_data["label_encoders"]
        self.scaler = model_data["scaler"]
        self.feature_names = list(model_data["feature_names"])
        self.reverse_label_mapping = model_data["reverse_label_mapping"]
        self.model_id = model_id
        self.model_sha256: str | None = None
        self.label_encoder = self.label_encoders.get("target_encoder")
        if self.label_encoder is None or not self.feature_names:
            raise ModelLoadError("Model artifact has no target encoder or selected feature list.")

        scaler_features = getattr(self.scaler, "feature_names_in_", None)
        self.numeric_features = list(scaler_features) if scaler_features is not None else [
            feature for feature in KDD_FEATURES
            if feature not in (*CATEGORICAL_FEATURES, "num_outbound_cmds")
        ]
        self.input_features = list(dict.fromkeys([*self.numeric_features, *CATEGORICAL_FEATURES]))
        class_ids = list(getattr(self.model, "classes_", range(len(self.reverse_label_mapping))))
        self.class_labels = {int(class_id): self.decode(class_id) for class_id in class_ids}

    @classmethod
    def from_path(cls, path: str | Path) -> "NslKddPredictor":
        model_path = Path(path).expanduser().resolve()
        if not model_path.is_file():
            raise ModelLoadError(f"NSL-KDD model artifact was not found at {model_path}.")
        # This is a pickle-based artifact from the explicitly configured local model source.
        # Do not accept model files through an API request.
        try:
            artifact_bytes = model_path.read_bytes()
            model_data = pickle.loads(artifact_bytes)
        except Exception as exc:
            raise ModelLoadError(f"Could not load NSL-KDD model: {exc}") from exc
        if not isinstance(model_data, dict):
            raise ModelLoadError("The NSL-KDD model artifact must contain a model dictionary.")
        predictor = cls(model_data, f"ml-cyber-threat-detector-nsl-kdd-{model_path.stem}")
        predictor.model_sha256 = hashlib.sha256(artifact_bytes).hexdigest()
        return predictor

    def decode(self, mapped_class: Any) -> str:
        original_encoded = self.reverse_label_mapping[int(mapped_class)]
        return str(self.label_encoder.inverse_transform([original_encoded])[0]).strip().rstrip(".")

    def info(self) -> dict[str, Any]:
        metrics_path = Path(__file__).resolve().parents[1] / "reports" / "nsl_kdd_test_metrics.json"
        test_metrics: dict[str, Any] = {}
        try:
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            if metrics.get("model_sha256") == self.model_sha256:
                test_metrics = metrics
        except (OSError, json.JSONDecodeError):
            pass
        return {
            "status": "active",
            "model_name": "XGBoost (NSL-KDD)",
            "model_id": self.model_id,
            "threshold": None,
            "score_type": "predicted_class_confidence",
            "score_description": "The score is the model confidence for its predicted class, not a confirmed attack.",
            "feature_names": self.input_features,
            "feature_count": len(KDD_FEATURES),
            "selected_feature_count": len(self.feature_names),
            "class_count": len(self.label_encoder.classes_),
            "test_accuracy": test_metrics.get("accuracy"),
            "test_accuracy_scope": test_metrics.get("accuracy_scope"),
            "test_rows": test_metrics.get("test_rows"),
            "full_test_accuracy": test_metrics.get("full_test_accuracy"),
            "full_test_rows": test_metrics.get("full_test_rows"),
            "supported_families": ["Normal", "DoS", "Probe", "R2L", "U2R"],
            "dataset_info": {"name": "NSL-KDD", "features": len(KDD_FEATURES)},
        }

    def _prepare(self, rows: list[dict[str, Any]]) -> pd.DataFrame:
        normalized_rows: list[dict[str, Any]] = []
        for row_number, row in enumerate(rows, start=1):
            normalized: dict[str, Any] = {}
            for key, value in row.items():
                name = str(key).strip().lower()
                if name == "protocol":
                    name = "protocol_type"
                if name in normalized:
                    raise ValueError(f"Row {row_number} has duplicate feature '{name}'.")
                normalized[name] = value
            missing = [name for name in self.input_features if name not in normalized]
            if missing:
                raise ValueError(
                    "CSV is missing required NSL-KDD features: " + ", ".join(missing[:12])
                )
            normalized_rows.append({name: normalized[name] for name in self.input_features})

        frame = pd.DataFrame(normalized_rows, columns=self.input_features)
        for feature in self.numeric_features:
            frame[feature] = pd.to_numeric(frame[feature], errors="coerce").replace(
                [np.inf, -np.inf], np.nan
            )
        means = getattr(self.scaler, "mean_", np.zeros(len(self.numeric_features)))
        fill_values = dict(zip(self.numeric_features, means))
        frame[self.numeric_features] = frame[self.numeric_features].fillna(fill_values)
        for feature in CATEGORICAL_FEATURES:
            encoder = self.label_encoders[feature]
            known_values = set(encoder.classes_)
            values = frame[feature].map(lambda value: str(value).strip().lower())
            fallback = str(encoder.classes_[0])
            values = values.map(lambda value: value if value in known_values else fallback)
            frame[feature] = encoder.transform(values)

        scaled_numeric = self.scaler.transform(frame[self.numeric_features].astype(float))
        for position, feature in enumerate(self.numeric_features):
            frame[feature] = scaled_numeric[:, position]
        missing_selected = [name for name in self.feature_names if name not in frame.columns]
        if missing_selected:
            raise ModelLoadError(
                "Preprocessing does not provide selected model features: " + ", ".join(missing_selected)
            )
        return frame.loc[:, self.feature_names]

    def predict_many(self, rows: list[dict[str, Any]], row_offset: int = 0) -> list[dict[str, Any]]:
        if not rows:
            raise ValueError("At least one network connection is required.")
        features = self._prepare(rows)
        mapped_predictions = np.asarray(self.model.predict(features.to_numpy())).reshape(-1)
        probabilities = np.asarray(self.model.predict_proba(features.to_numpy()))
        results = []
        for index, mapped_prediction in enumerate(mapped_predictions):
            predicted_label = self.decode(mapped_prediction).lower()
            category = ATTACK_CATEGORIES.get(predicted_label, "Unknown")
            predicted_column = next(
                (column for column, class_id in enumerate(self.model.classes_)
                 if int(class_id) == int(mapped_prediction)),
                int(mapped_prediction),
            )
            confidence = float(probabilities[index, predicted_column])
            malicious = predicted_label != "normal"
            severity = None
            if malicious:
                severity = "High" if confidence > 0.85 else "Medium" if confidence >= 0.60 else "Low"
            results.append({
                "row_index": row_offset + index,
                "score": confidence,
                "score_type": "predicted_class_confidence",
                "threshold": None,
                "is_malicious_prediction": malicious,
                "attack_family": category,
                "predicted_label": predicted_label,
                "family_score": confidence,
                "severity": severity,
                "model_id": self.model_id,
            })
        return results
