"""Request models and validation helpers for flow inference."""

from __future__ import annotations

import math
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FlowValidationError(ValueError):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}


def normalize_feature_key(value: str) -> str:
    return " ".join(value.strip().split())


class FlowPayload(BaseModel):
    """One flow whose numeric features use the dataset's original column names."""

    model_config = ConfigDict(extra="ignore")

    features: dict[str, Any] = Field(default_factory=dict, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def validate_feature_mapping(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            raise FlowValidationError("invalid_flow", "Each flow must be a JSON object.")
        if len(value) > 500:
            raise FlowValidationError(
                "too_many_features",
                "A flow may contain at most 500 feature fields.",
                {"feature_count": len(value), "maximum": 500},
            )
        normalized: dict[str, str] = {}
        for key, feature_value in value.items():
            if not isinstance(key, str):
                raise FlowValidationError("invalid_feature_name", "Feature names must be strings.")
            key_norm = normalize_feature_key(key)
            if not key_norm:
                raise FlowValidationError("invalid_feature_name", "Feature names cannot be blank.")
            if key_norm in normalized:
                raise FlowValidationError(
                    "duplicate_feature",
                    f"Feature names {normalized[key_norm]!r} and {key!r} collide after normalization.",
                )
            normalized[key_norm] = key
            if isinstance(feature_value, bool) or (
                feature_value is not None and not isinstance(feature_value, (int, float))
            ):
                raise FlowValidationError(
                    "invalid_feature_value",
                    f"Feature {key!r} must be a JSON number or null.",
                )
            if isinstance(feature_value, float) and not math.isfinite(feature_value):
                raise FlowValidationError(
                    "invalid_feature_value",
                    f"Feature {key!r} must be finite; use null for missing or infinite values.",
                )
        return {"features": value}

    @property
    def flow_features(self) -> dict[str, Any]:
        return self.features
