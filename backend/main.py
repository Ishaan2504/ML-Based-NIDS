"""FastAPI adapter for the NSL-KDD XGBoost model and the existing React UI."""

from __future__ import annotations

import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.nsl_kdd_predictor import KDD_COLUMNS, KDD_FEATURES, ModelLoadError, NslKddPredictor

VERSION = "0.3.0"
logger = logging.getLogger("nids.api")


def _allowed_origins() -> list[str]:
    value = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return [origin.strip() for origin in value.split(",") if origin.strip()]


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", str(uuid.uuid4()))


def _error(code: str, message: str, request: Request, status: int = 422,
           details: dict[str, Any] | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
                "request_id": _request_id(request),
            }
        },
        headers={"X-Request-ID": _request_id(request)},
    )


def _has_header(file: UploadFile) -> bool:
    file.file.seek(0)
    first = pd.read_csv(
        file.file, header=None, nrows=1, skipinitialspace=True,
        encoding="utf-8-sig", encoding_errors="replace",
    )
    file.file.seek(0)
    if first.empty:
        return False
    values = {str(value).strip().lower() for value in first.iloc[0].tolist()}
    return "duration" in values and bool({"protocol_type", "protocol"} & values)


def _read_chunks(file: UploadFile, predictor: NslKddPredictor):
    has_header = _has_header(file)
    file.file.seek(0)
    chunks = pd.read_csv(
        file.file,
        header=0 if has_header else None,
        skipinitialspace=True,
        chunksize=1000,
        encoding="utf-8-sig",
        encoding_errors="replace",
        low_memory=False,
    )
    for frame in chunks:
        if frame.empty:
            continue
        if len(frame.columns) > 100:
            raise ValueError("NSL-KDD CSV must contain at most 43 columns.")
        if has_header:
            frame.columns = [str(column).strip().lower() for column in frame.columns]
            frame = frame.rename(columns={"protocol": "protocol_type"})
        else:
            count = len(frame.columns)
            if count not in (len(KDD_FEATURES), len(KDD_FEATURES) + 1, len(KDD_COLUMNS)):
                raise ValueError(
                    f"Headerless NSL-KDD rows must have 41, 42, or 43 columns; found {count}."
                )
            frame.columns = KDD_COLUMNS[:count]
        if frame.columns.duplicated().any():
            raise ValueError("CSV contains duplicate column names.")
        missing = [feature for feature in predictor.input_features if feature not in frame.columns]
        if missing:
            raise ValueError(
                "CSV is missing required NSL-KDD features: " + ", ".join(missing[:12])
            )
        for feature in ("protocol_type", "service", "flag"):
            frame[feature] = frame[feature].map(
                lambda value: value.strip() if isinstance(value, str) else value
            )
        yield frame


def create_app(model_path: str | Path | None = None) -> FastAPI:
    default_model_path = Path(__file__).resolve().parents[1] / "models" / "ml_ctd" / "xgboost_model.pkl"
    configured_model_path = Path(
        model_path or os.getenv("MLCTD_MODEL_PATH", str(default_model_path))
    ).expanduser().resolve()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        application.state.predictor = None
        application.state.model_error = None
        try:
            application.state.predictor = NslKddPredictor.from_path(configured_model_path)
        except Exception as exc:
            logger.exception("NSL-KDD model could not be loaded from %s", configured_model_path)
            application.state.model_error = str(exc)
        yield

    application = FastAPI(
        title="ML Cyber Threat Detector API",
        description=(
            "Local API adapter for the NSL-KDD XGBoost model. "
            "It preserves the existing React dashboard API contract."
        ),
        version=VERSION,
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins(),
        # Vite may choose another port when its default port is already occupied.
        # Keep browser access limited to local development origins in that case.
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Key", "X-Request-ID"],
    )

    @application.middleware("http")
    async def request_context(request: Request, call_next):
        request.state.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        max_bytes = int(os.getenv("MAX_REQUEST_BYTES", str(500 * 1024 * 1024)))
        content_length = request.headers.get("content-length")
        if content_length and content_length.isdigit() and int(content_length) > max_bytes:
            return _error(
                "file_too_large", "Request exceeds the configured upload limit.", request,
                status=413, details={"maximum_bytes": max_bytes},
            )
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Process-Time"] = f"{time.perf_counter() - started:.6f}"
        return response

    @application.exception_handler(Exception)
    async def internal_error(request: Request, exc: Exception):
        logger.exception("Unhandled API error request_id=%s", _request_id(request))
        return _error("internal_error", "The request could not be completed.", request, status=500)

    def require_predictor(request: Request) -> NslKddPredictor:
        predictor = getattr(request.app.state, "predictor", None)
        if predictor is None:
            raise ModelLoadError(getattr(request.app.state, "model_error", None) or "Model is not loaded.")
        return predictor

    @application.exception_handler(ModelLoadError)
    async def model_error(request: Request, exc: ModelLoadError):
        return _error("model_not_loaded", str(exc), request, status=503)

    @application.exception_handler(ValueError)
    async def invalid_input(request: Request, exc: ValueError):
        return _error("invalid_input", str(exc), request, status=422)

    @application.get("/health", summary="API and model readiness")
    def health(request: Request) -> dict[str, Any]:
        predictor = getattr(request.app.state, "predictor", None)
        return {
            "status": "online" if predictor else "degraded",
            "model_loaded": predictor is not None,
            "mode": "offline-analysis",
            "version": VERSION,
            "message": None if predictor else getattr(request.app.state, "model_error", None),
        }

    @application.get("/model/info", summary="Active NSL-KDD model metadata")
    def model_info(request: Request) -> dict[str, Any]:
        predictor = getattr(request.app.state, "predictor", None)
        if predictor is None:
            return {
                "status": "not_loaded", "model_name": None, "model_id": None,
                "threshold": None, "score_type": None, "feature_names": [],
                "feature_count": None, "selected_feature_count": None,
                "class_count": None, "test_accuracy": None, "test_accuracy_scope": None,
                "test_rows": None, "full_test_accuracy": None, "full_test_rows": None,
                "supported_families": [],
                "message": getattr(request.app.state, "model_error", None),
            }
        return predictor.info()

    @application.post("/predict", summary="Predict one NSL-KDD connection")
    def predict(payload: dict[str, Any], request: Request) -> Any:
        predictor = require_predictor(request)
        features = payload.get("features", payload)
        if not isinstance(features, dict):
            return _error("invalid_flow", "Flow features must be a JSON object.", request)
        return predictor.predict_many([features])[0]

    @application.post("/predict/batch", summary="Predict a batch of NSL-KDD connections")
    def predict_batch(payload: dict[str, Any], request: Request) -> Any:
        flows = payload.get("flows")
        if not isinstance(flows, list) or not flows:
            raise ValueError("The request must contain a non-empty flows array.")
        if len(flows) > 10_000:
            return _error("batch_too_large", "A batch may contain at most 10,000 rows.", request, 413)
        normalized = [flow.get("features", flow) if isinstance(flow, dict) else flow for flow in flows]
        if not all(isinstance(flow, dict) for flow in normalized):
            raise ValueError("Each flow in the flows array must be a JSON object.")
        predictor = require_predictor(request)
        predictions = predictor.predict_many(normalized)
        malicious = sum(item["is_malicious_prediction"] for item in predictions)
        return {
            "total_flows": len(predictions), "malicious_count": malicious,
            "benign_count": len(predictions) - malicious,
            "predictions": predictions, "model_id": predictor.model_id,
        }

    @application.post("/analyze/csv", summary="Analyze an NSL-KDD CSV")
    async def analyze_csv(request: Request, file: UploadFile = File(...)) -> Any:
        predictor = require_predictor(request)
        if not file.filename or Path(file.filename).suffix.lower() not in (".csv", ".txt"):
            return _error("invalid_file_type", "Upload an NSL-KDD CSV or TXT file.", request)
        try:
            total_flows = 0
            malicious_count = 0
            prediction_breakdown: dict[tuple[str, str], int] = {}
            preview: list[dict[str, Any]] = []
            for frame in _read_chunks(file, predictor):
                rows = frame.to_dict(orient="records")
                predictions = predictor.predict_many(rows, row_offset=total_flows)
                malicious_count += sum(item["is_malicious_prediction"] for item in predictions)
                for item in predictions:
                    key = (str(item["predicted_label"]), str(item["attack_family"]))
                    prediction_breakdown[key] = prediction_breakdown.get(key, 0) + 1
                total_flows += len(predictions)
                if len(preview) < 100:
                    preview.extend(predictions[:100 - len(preview)])
            if not total_flows:
                return _error("empty_csv", "The uploaded file contains no connection rows.", request)
            return {
                "source_file": Path(file.filename).name,
                "total_flows": total_flows,
                "malicious_count": malicious_count,
                "benign_count": total_flows - malicious_count,
                "model_id": predictor.model_id,
                "feature_count": len(KDD_FEATURES),
                "prediction_breakdown": [
                    {"prediction": label, "category": family, "count": count}
                    for (label, family), count in sorted(
                        prediction_breakdown.items(), key=lambda entry: (-entry[1], entry[0][0])
                    )
                ],
                "preview": preview,
            }
        except (ValueError, pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError) as exc:
            return _error("invalid_csv", str(exc), request)

    return application


app = create_app()
