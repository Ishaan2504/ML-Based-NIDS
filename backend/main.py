"""FastAPI application for the local, offline NIDS dashboard."""

from __future__ import annotations

import hmac
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.predictor import Predictor
from backend.schemas.flow import FlowPayload, FlowValidationError

VERSION = "0.2.0"
logger = logging.getLogger("nids.api")


def _allowed_origins() -> list[str]:
    value = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return [origin.strip() for origin in value.split(",") if origin.strip()]


def create_app(model_dir: str | Path | None = None) -> FastAPI:
    configured_model_dir = Path(model_dir or os.getenv("MODEL_DIR", "models")).resolve()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        application.state.predictor = None
        application.state.model_error = None
        try:
            application.state.predictor = Predictor.from_dir(configured_model_dir)
        except Exception as exc:
            # A missing or invalid bundle is a supported degraded mode. The API
            # remains useful for health checks and the dashboard can explain why
            # analysis is unavailable.
            logger.exception("Model bundle could not be loaded from %s", configured_model_dir)
            application.state.model_error = str(exc)
        yield

    application = FastAPI(
        title="Sentinel NIDS API",
        description=(
            "Local API for offline analysis of recorded network flows. "
            "Predictions are model outputs, not confirmed attacks."
        ),
        version=VERSION,
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Key", "X-Request-ID"],
    )

    @application.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        started = time.perf_counter()
        max_bytes = int(os.getenv("MAX_REQUEST_BYTES", str(500 * 1024 * 1024)))
        content_length = request.headers.get("content-length")
        if content_length and content_length.isdigit() and int(content_length) > max_bytes:
            response = JSONResponse(
                status_code=413,
                content={"error": {"code": "payload_too_large", "message": "Request body exceeds the configured size limit.", "request_id": request_id}},
                headers={"X-Request-ID": request_id},
            )
            return response
        api_key = os.getenv("API_KEY", "")
        if api_key and request.url.path in {"/predict", "/predict/batch", "/explain"}:
            supplied = request.headers.get("X-API-Key", "")
            if not hmac.compare_digest(supplied, api_key):
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": {
                            "code": "invalid_api_key",
                            "message": "A valid X-API-Key header is required.",
                            "request_id": request_id,
                        }
                    },
                    headers={"X-Request-ID": request_id},
                )
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            json.dumps(
                {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                },
                separators=(",", ":"),
            )
        )
        return response

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        details = exc.errors()
        custom_error = next(
            (
                item.get("ctx", {}).get("error")
                for item in details
                if getattr(item.get("ctx", {}).get("error"), "code", None)
            ),
            None,
        )
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": getattr(custom_error, "code", "invalid_request"),
                    "message": str(custom_error) if custom_error else "The request body does not match the API schema.",
                    "details": [
                        {
                            "location": error.get("loc", []),
                            "message": error.get("msg", "Invalid value."),
                            "type": error.get("type"),
                        }
                        for error in details
                    ],
                    "request_id": request_id,
                }
            },
            headers={"X-Request-ID": request_id},
        )

    @application.exception_handler(FlowValidationError)
    async def flow_validation_error(request: Request, exc: FlowValidationError):
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": exc.code,
                    "message": str(exc),
                    "details": exc.details,
                    "request_id": request_id,
                }
            },
            headers={"X-Request-ID": request_id},
        )

    def require_predictor(request: Request) -> Predictor:
        predictor = getattr(request.app.state, "predictor", None)
        if predictor is None:
            message = getattr(request.app.state, "model_error", None)
            raise ApiUnavailable(message or "No verified model bundle is configured.")
        return predictor

    @application.exception_handler(ApiUnavailable)
    async def unavailable_error(request: Request, exc: ApiUnavailable):
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "model_not_loaded",
                    "message": str(exc),
                    "request_id": request_id,
                }
            },
            headers={"X-Request-ID": request_id},
        )

    @application.exception_handler(Exception)
    async def internal_error(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        logger.exception("Unhandled API error request_id=%s", request_id)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "The request could not be completed.",
                    "request_id": request_id,
                }
            },
            headers={"X-Request-ID": request_id},
        )

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

    @application.get("/model/info", summary="Active model metadata")
    def model_info(request: Request) -> dict[str, Any]:
        predictor = getattr(request.app.state, "predictor", None)
        if predictor is None:
            return {
                "status": "not_loaded",
                "model_name": None,
                "model_id": None,
                "threshold": None,
                "score_type": None,
                "score_description": (
                    "A model score ranks flows by how attack-like the model finds them; "
                    "it is not the probability that an attack occurred."
                ),
                "feature_names": [],
                "feature_count": None,
                "supported_families": [],
                "version_mismatch": None,
                "message": getattr(request.app.state, "model_error", None),
            }
        return predictor.info()

    @application.get("/model/benchmark", summary="Local model comparison report")
    def model_benchmark(request: Request) -> dict[str, Any]:
        require_predictor(request)
        report_path = Path(__file__).resolve().parents[1] / "reports" / "benchmark_metrics.json"
        if not report_path.is_file():
            raise ApiUnavailable("No model benchmark report is available.")
        return json.loads(report_path.read_text(encoding="utf-8"))

    @application.post("/predict", summary="Predict one recorded network flow")
    def predict(flow: FlowPayload, request: Request) -> dict[str, Any]:
        predictor = require_predictor(request)
        return predictor.predict_one(flow.features)

    @application.post("/predict/batch", summary="Predict a batch of recorded network flows")
    def predict_batch(payload: dict[str, list[FlowPayload]], request: Request) -> dict[str, Any]:
        flows = payload.get("flows")
        if flows is None:
            raise FlowValidationError("missing_flows", "The request must contain a flows array.")
        if not flows:
            raise FlowValidationError("empty_input", "At least one flow is required.")
        if len(flows) > 10_000:
            raise FlowValidationError("batch_too_large", "A batch may contain at most 10,000 flows.")
        predictor = require_predictor(request)
        predictions = predictor.predict_many([flow.features for flow in flows])
        malicious = sum(item["is_malicious_prediction"] for item in predictions)
        return {
            "total_flows": len(predictions),
            "malicious_count": malicious,
            "benign_count": len(predictions) - malicious,
            "predictions": predictions,
            "model_id": predictor.model_id,
        }

    @application.post("/analyze/csv", summary="Analyze a CSV of recorded network flows")
    async def analyze_csv(request: Request, file: UploadFile = File(...)) -> dict[str, Any]:
        predictor = require_predictor(request)
        if not file.filename or Path(file.filename).suffix.lower() != ".csv":
            raise FlowValidationError("invalid_file_type", "Upload a .csv file.")
        max_bytes = int(os.getenv("MAX_REQUEST_BYTES", str(500 * 1024 * 1024)))
        if file.size is not None and file.size > max_bytes:
            raise FlowValidationError("file_too_large", "CSV exceeds the configured upload limit.",
                                      {"maximum_bytes": max_bytes})
        try:
            file.file.seek(0)
            chunks = pd.read_csv(file.file, low_memory=False, chunksize=1000, encoding="cp1252",
                                 encoding_errors="replace")
            total_flows = 0
            malicious_count = 0
            preview: list[dict[str, Any]] = []
            expected_features = {" ".join(name.strip().split()) for name in predictor.feature_names}
            for frame in chunks:
                if frame.empty:
                    continue
                if len(frame.columns) > 500:
                    raise FlowValidationError("too_many_features", "CSV may contain at most 500 columns.")
                frame.columns = [" ".join(str(column).strip().split()) for column in frame.columns]
                if frame.columns.duplicated().any():
                    raise FlowValidationError("duplicate_feature", "CSV contains duplicate feature names.")
                if total_flows == 0:
                    missing = sorted(expected_features - set(frame.columns))
                    if missing:
                        raise FlowValidationError(
                            "missing_features", "CSV is missing required features for the active model.",
                            {"missing_features": missing[:30], "missing_count": len(missing)},
                        )
                frame = frame.apply(pd.to_numeric, errors="coerce")
                frame = frame.replace([float("inf"), float("-inf")], float("nan"))
                frame = frame.astype(object).where(pd.notna(frame), None)
                scored = predictor.predict_many(frame.to_dict(orient="records"))
                malicious_count += sum(item["is_malicious_prediction"] for item in scored)
                total_flows += len(scored)
                if len(preview) < 100:
                    preview.extend(scored[:100 - len(preview)])
        except FlowValidationError:
            raise
        except (ValueError, pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError) as exc:
            raise FlowValidationError("invalid_csv", "Could not read the uploaded CSV file.") from exc
        if total_flows == 0:
            raise FlowValidationError("empty_csv", "The uploaded CSV contains no flow rows.")
        return {
            "source_file": Path(file.filename).name,
            "total_flows": total_flows,
            "malicious_count": malicious_count,
            "benign_count": total_flows - malicious_count,
            "model_id": predictor.model_id,
            "feature_count": len(predictor.feature_names),
            "preview": preview,
        }

    @application.post("/explain", summary="Explain one model prediction")
    def explain(flow: FlowPayload, request: Request) -> JSONResponse:
        # Explanations are deliberately unavailable until a verified model and
        # supported explainer have both been implemented in the inference bundle.
        require_predictor(request)
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        return JSONResponse(
            status_code=501,
            content={
                "error": {
                    "code": "explanation_unavailable",
                    "message": "This model bundle does not expose a verified local explainer yet.",
                    "request_id": request_id,
                }
            },
        )

    return application


class ApiUnavailable(Exception):
    """Raised when prediction is requested before a trusted bundle is ready."""


app = create_app()
