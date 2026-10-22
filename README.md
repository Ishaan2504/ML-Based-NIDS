# Sentinel Network Intrusion Detection System (NIDS)


**Sentinel NIDS** is a powerful, open‑source network intrusion detection system that analyzes offline NSL‑KDD flow records using a pretrained XGBoost multiclass model. It provides a modern React dashboard and a FastAPI backend for fast, interactive analysis of up to ten CSV/TXT files at a time.

---
a
## 📚 Table of Contents
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Demo & Screenshots](#demo--screenshots)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Training & Evaluation](#training--evaluation)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)
- [References](#references)

---

## ✨ Features
- **Offline flow analysis** – No live packet capture required.
- **Batch processing** – Upload up to 10 NSL‑KDD CSV/TXT files in a single run.
- **Rich visualisations** – Interactive class distribution charts, threat‑ratio gauges, and preview tables.
- **Model introspection** – View model metadata, supported labels, and evaluation scores directly in the UI.
- **Extensible pipeline** – Separate CIC‑IDS2017 benchmark scripts for research extensions.
- **Docker‑ready** – Easy containerisation for reproducible deployments (see `Dockerfile` in `backend`).

---

## 🛠️ Technology Stack
| Layer | Technology |
|---|---|
| UI | React 19, TypeScript, Vite, Recharts, Lucide |
| API | Python 3.10‑3.12, FastAPI, Pydantic, Uvicorn |
| Model & preprocessing | XGBoost, pandas, NumPy, scikit‑learn |
| Dataset | NSL‑KDD (offline) |
| Research pipeline | CIC‑IDS2017 benchmark (scripts) |

---

## 🚀 Quick Start (Windows)
```powershell
# 1️⃣ Clone the repo
git clone https://github.com/Ishaan2504/ML-Based-NIDS.git
cd ML-Based-NIDS

# 2️⃣ Create a virtual environment and install Python deps
python -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3️⃣ Start the FastAPI backend (default: http://127.0.0.1:8000)
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
In a **second terminal** run the frontend:
```powershell
cd frontend
npm install
npm run dev   # Vite dev server → http://localhost:5173
```
The UI will automatically point to the local API. Set `VITE_API_URL` env‑var if you need a different address.

---

## 📂 Project Structure
```
ML-Based-NIDS/
├─ backend/                 # FastAPI service
│   ├─ main.py
│   └─ nsl_kdd_predictor.py
├─ config/                  # Pipeline & attack‑family configs
├─ data/raw/nsl_kdd/        # Place KDDTrain+/KDDTest+ here (git‑ignored)
├─ docs/                    # Architecture diagrams, banners, screenshots
├─ frontend/                # React dashboard (Vite)
├─ models/ml_ctd/           # Pre‑trained XGBoost model (pickle)
├─ reports/                 # Evaluation & benchmark JSON files
├─ scripts/                 # Training, evaluation, CIC‑IDS pipeline
├─ tests/                   # Unit & integration tests
├─ requirements.txt
├─ pyproject.toml
└─ README.md                # THIS FILE
```

---

## 📈 Training & Evaluation
```bash
# Train the XGBoost model on NSL‑KDD
python scripts/train_nsl_kdd_model.py

# Evaluate on the held‑out test split
python -m scripts.evaluate_nsl_kdd_model
```
Metrics are written to `reports/nsl_kdd_test_metrics.json` and automatically linked in the dashboard UI.

### CIC‑IDS2017 Research Pipeline
```bash
# After placing CIC‑IDS2017 CSVs under data/raw/cicids2017/
python scripts/run_pipeline.py --fast   # Quick smoke test
python scripts/run_pipeline.py          # Full benchmark (writes reports/benchmark_metrics.json)
```

---

## 📡 API Reference
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check and model readiness |
| `GET` | `/model/info` | Returns model metadata, supported labels, and evaluation scores |
| `POST` | `/predict` | Predict a single NSL‑KDD connection (JSON payload) |
| `POST` | `/predict/batch` | Predict up to 10 000 connections in a single request |
| `POST` | `/analyze/csv` | Analyse an uploaded CSV/TXT file (used by the dashboard) |

---

## 🤝 Contributing
Contributions are welcome! Please:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feat/your-feature`).
3. Run the full test suite:
   ```bash
   python -m pytest
   ```
4. Open a pull request against `main` with a clear description of your changes.

All code follows the Black formatter and is linted with Ruff.

---

## 📄 License
This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

---

## 📚 References
- NSL‑KDD dataset: https://www.unb.ca/cic/datasets/nsl.html
- CIC‑IDS2017 dataset: https://www.unb.ca/cic/datasets/ids-2017.html
- XGBoost: https://xgboost.readthedocs.io/

---

*Feel free to raise issues, suggest features, or contribute improvements!*

Sentinel NIDS is a local web application for analyzing **recorded NSL-KDD network connection data**. It pairs a React dashboard with a FastAPI service and a trained multiclass XGBoost model. Upload one or several CSV/TXT files to get a separate prediction summary for each file, including normal and threat counts, threat ratio, predicted classes, and attack families.

> **Scope:** This is an offline flow-analysis project. It does not capture live network traffic, inspect packets, or confirm that a prediction is a real attack. Treat predictions as a triage aid.

## What the current app does

- Reports API/model readiness and active model details in the dashboard.
- Accepts NSL-KDD CSV or TXT files with the 41 connection features. Headers may be included; the original headerless 41-, 42-, and 43-column formats are also supported. Optional `label` and `difficulty` columns are ignored for prediction.
- Allows up to 10 files to be selected in one batch. Files are analyzed one at a time and results are kept separate, with a comparison table and expandable per-file summaries.
- Displays per-file flow counts, predicted benign/malicious counts, threat ratio, class breakdown, and an example preview. The API processes files in chunks and returns up to 100 preview predictions per file.
- Provides single-flow and batch JSON prediction endpoints in addition to CSV analysis.

## Technology

| Layer | Technology |
|---|---|
| UI | React 19, TypeScript, Vite, Recharts, Lucide |
| API | Python, FastAPI, Pydantic, Uvicorn |
| Model and preprocessing | XGBoost, pandas, NumPy, scikit-learn |
| Active dataset | NSL-KDD |
| Separate research workflow | CIC-IDS2017 binary-model benchmark script |

## Model and evaluation

The active model is an XGBoost multiclass classifier trained by `scripts/train_nsl_kdd_model.py` on the 125,973 rows in `KDDTrain+`, using the 23 labels represented in that training file. The serialized model is loaded from `models/ml_ctd/xgboost_model.pkl`.

The current local evaluation on the held-out `KDDTest+` split reports:

| Evaluation scope | Correct / total | Accuracy |
|---|---:|---:|
| Rows whose labels are represented by the model | 16,293 / 18,794 | 86.7% |
| All held-out rows, exact label match | 16,293 / 22,544 | 72.3% |

The full-split score is lower because 3,750 `KDDTest+` rows have labels that do not appear in `KDDTrain+`. The dashboard reports the supported-label accuracy and also shows the full-split score. Metrics are read only when `reports/nsl_kdd_test_metrics.json` contains the SHA-256 hash of the loaded model, so retraining requires reevaluation before current accuracy is available. These are benchmark results, not a guarantee of performance on other networks.

The raw NSL-KDD data is not included in the repository. Obtain the dataset through the [Canadian Institute for Cybersecurity NSL-KDD page](https://www.unb.ca/cic/datasets/nsl.html) and place the files at:

```text
data/raw/nsl_kdd/KDDTrain+.txt
data/raw/nsl_kdd/KDDTest+.txt
```

Raw data and local intermediate files are git-ignored.

## Quick start

Use Python 3.10–3.12 and Node.js 20 or newer.

### 1. Install Python dependencies

From the repository root:

```powershell
# Windows PowerShell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

```bash
# macOS / Linux
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Start the API

From the repository root, in one terminal:

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

The API documentation is available at `http://127.0.0.1:8000/docs`.

### 3. Start the dashboard

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite (normally `http://localhost:5173`). The default API URL is `http://127.0.0.1:8000`. Set `VITE_API_URL` before starting Vite to use a different API address. The API's local CORS configuration allows localhost and 127.0.0.1 development origins.

## Uploading files

1. Open **Traffic Analysis Lab** in the dashboard.
2. Select up to 10 `.csv` and/or `.txt` NSL-KDD files. Each file may be at most 500 MB.
3. Choose **Analyze files**. The UI sends each file to the API sequentially and shows progress.
4. Review the comparison table, then expand any file for its class chart and prediction breakdown.

The API accepts headed CSVs with NSL-KDD feature names or headerless files containing 41 feature columns, optionally followed by `label` and `difficulty`. The categorical fields are `protocol_type`, `service`, and `flag`. Files should contain the model's expected NSL-KDD features; arbitrary CSVs (for example, CIC-IDS2017 rows) are not interchangeable with NSL-KDD.

The API does not retain uploaded files. It analyzes up to 1,000 rows at a time and returns aggregate per-class counts plus a preview of up to 100 rows. The default maximum HTTP request size is 500 MB and can be adjusted with `MAX_REQUEST_BYTES`.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | API and model readiness |
| `GET` | `/model/info` | Model, supported labels, features, and matching evaluation metrics |
| `POST` | `/predict` | Predict one NSL-KDD connection from a JSON object |
| `POST` | `/predict/batch` | Predict up to 10,000 connections in one JSON request |
| `POST` | `/analyze/csv` | Analyze one CSV/TXT upload; the UI calls this once per selected file |

## Training and evaluation

With the NSL-KDD files in `data/raw/nsl_kdd/`, train the active XGBoost model:

```bash
python scripts/train_nsl_kdd_model.py
```

Evaluate it on the separate held-out test file and refresh the model-hash-bound metrics:

```bash
python -m scripts.evaluate_nsl_kdd_model
```

Restart the API after training so it loads the new model artifact. Do not train on `KDDTest+`; it is reserved for evaluation.

### Separate CIC-IDS2017 research pipeline

`scripts/run_pipeline.py` is a separate binary classification experiment over CIC-IDS2017 CSV files. It compares Logistic Regression, Random Forest, Extra Trees, and XGBoost and writes benchmark metrics to `reports/benchmark_metrics.json`. It does **not** provide the multiclass NSL-KDD model used by the active dashboard API.

After placing CIC-IDS2017 CSVs under `data/raw/cicids2017/`, run:

```bash
python scripts/run_pipeline.py --fast  # quick smoke run; not final performance
python scripts/run_pipeline.py         # full experiment
```

## Repository layout

```text
ML PROJECT/
├── backend/
│   ├── main.py                       # FastAPI health, prediction, and CSV analysis routes
│   ├── nsl_kdd_predictor.py          # NSL-KDD preprocessing and model inference
│   ├── predictor.py                  # CIC-IDS research pipeline adapter
│   └── README.md                     # API-specific notes
├── config/                           # Pipeline and attack-family configuration
├── data/                             # Local datasets and intermediate data (git-ignored)
├── docs/                             # Architecture, assessment, dataset, and decision notes
├── frontend/
│   ├── src/App.tsx                   # Dashboard and multi-file analysis results
│   ├── src/lib/api.ts                # Browser-to-API calls and response types
│   └── src/styles/                   # Dashboard, responsive layout, and analysis styles
├── models/ml_ctd/                    # Active NSL-KDD XGBoost model artifact
├── reports/
│   ├── nsl_kdd_test_metrics.json     # Evaluation for the active model hash
│   └── benchmark_metrics.json        # CIC-IDS2017 research benchmark output
├── scripts/
│   ├── train_nsl_kdd_model.py        # Train the active NSL-KDD model
│   ├── evaluate_nsl_kdd_model.py     # Evaluate on held-out KDDTest+
│   └── run_pipeline.py               # Separate CIC-IDS2017 comparison workflow
├── src/nids/                         # Shared NIDS data and common utilities
├── tests/                            # Unit and API tests
├── requirements.txt                  # Python dependencies
└── pyproject.toml                    # Python package and tooling configuration
```

## Development checks

Build the dashboard:

```bash
cd frontend
npm run build
```

Python tests are configured in `pyproject.toml` and live under `tests/`. Run them from the repository root with `python -m pytest` after installing `requirements-dev.txt`.

## Responsible use and limitations

- This application scores offline flow records; it does not capture or monitor live network traffic.
- A predicted class or score is not a confirmed incident or a calibrated probability.
- The model is trained and evaluated on NSL-KDD. Network environments and newer attack behaviors may differ substantially.
- Evaluation labels absent from the training set cannot be directly learned as distinct classes by this model.
- Keep uploads and model artifacts local and use only trusted pickle files. Never load an untrusted serialized model.

## References

- [NSL-KDD dataset and documentation](https://www.unb.ca/cic/datasets/nsl.html)
- [CIC-IDS2017 dataset and documentation](https://www.unb.ca/cic/datasets/ids-2017.html)
