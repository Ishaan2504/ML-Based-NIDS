# NSL-KDD inference API

This FastAPI service adapts the trained XGBoost model from [ML-Cyber-Threat-Detector](https://github.com/ARYANJUMDE/ML-Cyber-Threat-Detector) for the React dashboard. The upstream project uses Streamlit as its UI, so this service provides HTTP endpoints for local model metadata and NSL-KDD inference.

## Model artifact

The service loads the local pickle at `models/ml_ctd/xgboost_model.pkl`, or the path set by `MLCTD_MODEL_PATH`. The upstream pre-trained pickle did not load with the XGBoost version installed in this workspace, so the local copy was retrained with `scripts/train_nsl_kdd_model.py` from the upstream NSL-KDD training/test files. To create a model in another checkout, download those dataset files and run:

```powershell
python scripts/train_nsl_kdd_model.py --train data/raw/nsl_kdd/KDDTrain+.txt
```

Download `KDDTrain+.txt` and `KDDTest+.txt` from the [NSL-KDD dataset page](https://www.unb.ca/cic/datasets/nsl-kdd.html) and place them at the paths in the command. The dataset files are not included in this repository. Do not accept or load model files uploaded through an API request.

The artifact uses Python pickle serialization. Only load a copy obtained from a source you trust. The upstream repository currently has no `LICENSE` file, so get permission before redistributing its model artifact or derived files.

## Start locally

From the repository root, install dependencies from `requirements.txt`, then start the API:

```powershell
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

The React dashboard runs separately from `frontend/` and uses `VITE_API_URL` (default `http://127.0.0.1:8000`). API docs are at `http://127.0.0.1:8000/docs`.

## CSV input

`POST /analyze/csv` accepts NSL-KDD connections with 41 feature columns, optionally followed by `label` and `difficulty`. Headerless rows may contain 41, 42, or 43 columns; headed CSVs may use the NSL-KDD column names. The required inputs include duration, protocol type, service, flag, byte counts, connection counters, and destination-host statistics. Categorical values are `protocol_type`, `service`, and `flag`. `label` and `difficulty` are ignored for prediction.

[`nsl_kdd_demo_upload.csv`](../nsl_kdd_demo_upload.csv) is a small synthetic example that can be uploaded from the dashboard.

The API reads at most 1,000 rows at a time, returns aggregate Normal/attack counts and up to 100 preview predictions, and does not save uploads. The local `MAX_REQUEST_BYTES` limit defaults to 500 MB. Predictions are model outputs, not confirmed attacks. The model predicts the NSL-KDD classes included in its trained artifact; the adapter maps those labels to Normal, DoS, Probe, R2L, or U2R families.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | API and model readiness |
| `GET` | `/model/info` | Model and input feature metadata |
| `POST` | `/predict` | Score one NSL-KDD connection |
| `POST` | `/predict/batch` | Score up to 10,000 connections |
| `POST` | `/analyze/csv` | Analyze a CSV/TXT of NSL-KDD rows |

The repository's CIC-IDS2017 training pipeline remains available as a separate experiment. It does not produce the model used by this API.

The model metadata includes test accuracy only when `reports/nsl_kdd_test_metrics.json` matches the active model's SHA-256 hash. The current value is 86.7% on 18,794 KDDTest+ rows with supported labels; full-split exact-label accuracy is 72.3% across all 22,544 rows. The model was trained on all 23 labels present in KDDTrain+; 3,750 test rows contain labels absent from the training split. Recalculate it with `python -m scripts.evaluate_nsl_kdd_model` after adding `KDDTest+.txt` to `data/raw/nsl_kdd/`.
