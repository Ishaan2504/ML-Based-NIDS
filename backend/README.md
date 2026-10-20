# FastAPI inference service

The service exposes the local offline inference API used by the SOC dashboard. It starts in degraded mode when there is no active, verified model bundle. In that state `/health` and `/model/info` remain available, while prediction requests return `503 model_not_loaded`. It does not generate placeholder predictions.

## Start locally

From the repository root, install the development dependencies and package, then run:

```powershell
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

OpenAPI documentation is available at `http://127.0.0.1:8000/docs`. The React dev server origin is allowed by default at `http://localhost:5173` and `http://127.0.0.1:5173`.

## Model bundle

Set `MODEL_DIR` to the local model directory if needed. The service reads the model ID from `MODEL_DIR/ACTIVE`, then requires `MODEL_DIR/<model_id>/bundle.joblib`, `bundle.sha256`, and `bundle_meta.json`. It verifies the bundle hash and schema before loading it. The model files must be trusted because joblib bundles use Python serialization. Never load a bundle supplied by an API request or uploaded CSV.

The bundle must provide `binary_pipeline`, `feature_names`, `threshold`, `schema_version`, and the metadata fields described in the technical specification. `multiclass_pipeline`, `family_classes`, `feature_ranges`, `severity_config`, and validation-derived `score_tier_edges` are optional. Predictions report a model score, not a calibrated probability. Severity stays null if validation-derived score-tier edges or family impact configuration are unavailable.

## API

`POST /predict` accepts a JSON object whose keys are dataset feature names. `POST /predict/batch` accepts `{"flows": [{...}, {...}]}`. Feature values must be JSON numbers or `null`; required features come from the active model bundle. Unknown fields are ignored and listed in the response. The batch limit is 10,000 records.

When `API_KEY` is set, include it as `X-API-Key` on `/predict`, `/predict/batch`, and `/explain`. Set `CORS_ORIGINS` to a comma-separated list of trusted browser origins when changing the frontend origin.

All responses include an `X-Request-ID`. Errors use an `error` object with `code`, `message`, and `request_id`. `/explain` currently returns `501 explanation_unavailable`; no feature attribution is fabricated.

The API is stateless: `/analyze/csv` scores a local uploaded CSV in 1,000-row chunks and returns aggregate counts plus a 100-row preview; it does not persist the upload or prediction rows. The default request limit is 500 MB and can be changed with `MAX_REQUEST_BYTES`. The CSV must contain every feature used by the active model. Blank, infinite, and nonnumeric cells are treated as missing and imputed by the trained pipeline. Extra columns such as `Label`, IDs, and timestamps are ignored by inference.
