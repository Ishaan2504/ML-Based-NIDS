# ML-Based Network Intrusion Detection System (NIDS)

An offline, dataset-driven network intrusion detection project for analysing recorded network-flow CSV files from CIC-IDS2017. The planned system classifies flows as benign or malicious, assigns predicted attack families, and presents analysis in a local SOC-style dashboard.

> **Status:** Project scaffold created; implementation and real-data evaluation have not been completed. Results: **Not yet generated.**

## Scope

- Validate and clean CIC-IDS2017 flow CSV files, then create leakage-aware train, validation, and test splits.
- Train and compare Logistic Regression, Random Forest, XGBoost, and Isolation Forest models, with binary and attack-family classification where specified.
- Select thresholds and models using validation data; reserve the test split for final evaluation after the model is frozen.
- Save a reusable inference bundle and expose it through a local FastAPI API.
- Explore saved runs and uploaded CSV analyses in a six-page Streamlit dashboard.
- Produce reports, downloadable predictions, and model explanations.

This version is offline analysis only. It does not capture packets, parse PCAP files, scan networks, monitor live traffic, or send uploaded data to third-party services. It is an educational/research project, not a production security product.


## Technology stack

The planned implementation uses Python 3.11; pandas, NumPy, and PyArrow for data handling; scikit-learn and XGBoost for machine learning; SHAP, Matplotlib, and Plotly for explanations and visualizations; FastAPI, Uvicorn, and Pydantic for the API; and Streamlit for the dashboard. Local file storage is the default, with PostgreSQL optional. pytest, pytest-cov, HTTPX, Ruff, and Black are planned for testing and code quality. See `requirements.txt` and `requirements-dev.txt` for the dependency ranges.

## Mini-project assessment

The repository tracks the 15-mark rubric and requested report outline in [`docs/ASSESSMENT.md`](docs/ASSESSMENT.md). The rubric covers data cleaning and splitting (3 marks), model comparison and analytics (4), UI deployment and cross-platform accessibility (4), and code quality/repository/report/submission (4). The report outline requires an introduction, a comparison of at least five recent papers, methodology, preprocessing, results, comparison of at least four models with metrics and figures, UI and deployment, and references.

Those are project requirements, not claims of completed work. Model results, literature review, deployment/accessibility evidence, report, and demo/viva materials remain outstanding. No fabricated results are included.
## Project status and results

No model metrics, dataset counts, alerts, or performance claims are available yet. They will remain **Not yet generated** until the pipeline writes the corresponding report artifacts. Once generated, results should be read from `reports/` and described with their dataset split and report source.

The project uses lab-generated CIC-IDS2017 traffic from 2017. Dataset artefacts, service/port shortcut risk, low-support attack classes, and uncalibrated model scores limit how results should be interpreted. A predicted alert is a model output, not a confirmed attack; scores are not calibrated attack probabilities unless calibration has been evaluated and reported.

## Requirements

- Python 3.11 (Python 3.10-3.12 supported)
- 8 GB RAM minimum; 16 GB recommended
- 10 GB free disk space recommended for dataset processing
- No GPU or paid services required

## Setup

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
pip install -e .
```

### Linux/macOS

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
pip install -e .
```

## Dataset setup

Download CIC-IDS2017 manually from the official Canadian Institute for Cybersecurity source, following its current terms. Place the dataset CSV files in `data/raw/cicids2017/`. See [`data/raw/cicids2017/README.txt`](data/raw/cicids2017/README.txt).

The pipeline must inspect the supplied files and write a schema report before proceeding. It stops if no CSV files are present, labels are unmapped, or schema requirements fail. Raw and processed data are excluded from version control. Do not commit the dataset or uploaded flow data.

Dataset reference: Sharafaldin, Lashkari, and Ghorbani, “Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization,” ICISSP 2018. See `docs/DATASET.md` for the citation and applicable dataset terms when completed.

## Running the project

The commands below describe the intended interface. The pipeline and services are not implemented in this scaffold yet.

```bash
# Validate and inspect the supplied dataset
python scripts/run_pipeline.py --stage validate

# Run the full pipeline in reduced-resource mode
python scripts/run_pipeline.py --fast

# Start the local API
uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Start the Streamlit SOC dashboard (in another terminal)
streamlit run frontend/app.py
```

The API is intended to provide `/health`, `/model/info`, `/predict`, `/predict/batch`, and `/explain`. The dashboard is intended to include Security Overview, Threat Alerts, Traffic Investigation, Network Activity, Model Performance, and Traffic Analysis Lab pages. Data-dependent views are disabled or clearly explained when required metadata is unavailable.

## Evaluation and data handling

- Fit learned preprocessing and models on the training split only.
- Use validation data for model selection and threshold choice.
- Freeze the selected model before running final test evaluation. The evaluation stage must refuse to overwrite `reports/test_metrics.json` unless explicitly forced.
- Never use synthetic/demo rows for reported model performance. Clearly label synthetic or demo material in its UI and metadata.
- Keep run artifacts local under `data/runs/`; treat uploaded IP addresses and flow records as sensitive.

## Repository structure

```text
.
├── config/                 # Central configuration, column aliases, label map
├── data/
│   ├── raw/cicids2017/     # Manually supplied source CSVs (git-ignored)
│   ├── interim/            # Per-file cleaned Parquet (git-ignored)
│   ├── processed/          # Train/validation/test Parquet (git-ignored)
│   └── runs/               # Local analysis runs (git-ignored)
├── models/                 # Serialized bundles and freeze marker (git-ignored)
├── reports/                # Generated validation/evaluation reports and figures
├── notebooks/              # Optional exploratory analysis only
├── src/nids/
│   ├── common/             # Config, paths, logging, shared errors
│   ├── data/               # Dataset adapters, load, validate, clean, split
│   ├── features/           # Feature selection and shared preprocessing
│   ├── training/           # Training, tuning, thresholds, calibration
│   ├── evaluation/         # Metrics, reports, plots
│   ├── inference/          # Bundles, prediction, severity, explanations
│   └── storage/            # File run store and optional PostgreSQL
├── backend/                # FastAPI app, routes, request/response schemas
├── frontend/               # Streamlit app, components, six pages
├── scripts/                # Pipeline and model utility entry points
├── tests/                  # Unit, API, integration tests, synthetic fixtures
├── docs/                   # Architecture, dataset, decisions, progress
└── README.md
```

## Roadmap

1. Scaffold, configuration, dataset loading, and validation report.
2. Cleaning, leakage-aware splitting, and baseline models.
3. Improved models, tuning, ablations, threshold selection, and frozen evaluation.
4. Inference bundle, predictor, and severity rules.
5. FastAPI backend.
6. Streamlit dashboard.
7. Explainability, safe downloads, and optional PostgreSQL.
8. Tests, documentation, and demo preparation.

Record phase decisions and acceptance checks in `docs/DECISIONS.md` and `docs/PROGRESS.md` as implementation proceeds.

## Future work

Any future live-monitoring feature requires written permission from the network owner, legal review of interception rules, data minimisation (such as hashing or truncating IP addresses), access control, retention limits, and an isolated environment before implementation begins.

