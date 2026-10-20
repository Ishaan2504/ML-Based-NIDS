# 🛡️ Sentinel NIDS: ML-Based Network Intrusion Detection System

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React 19" />
  <img src="https://img.shields.io/badge/TypeScript-5.7-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-v4-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white" alt="Tailwind CSS v4" />
  <img src="https://img.shields.io/badge/Dataset-CIC--IDS2017-orange?style=for-the-badge" alt="Dataset" />
  <img src="https://img.shields.io/badge/CI-GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white" alt="CI" />
</p>

---

## 📌 Executive Summary

**Sentinel NIDS** is a local application for offline analysis of recorded network-flow data from **CIC-IDS2017**. Its training command compares Logistic Regression, Random Forest, Extra Trees, and XGBoost, packages a selected binary classifier, and serves CSV predictions through a local API and dashboard.

The repository includes a local CIC-IDS2017 training command that compares Logistic Regression, Random Forest, Extra Trees, and XGBoost, selects a model using validation PR-AUC, reports held-out metrics, and writes a checksummed bundle for the FastAPI service. Reproducing the run requires the CIC-IDS2017 CSV files under `data/raw/cicids2017/`. The service does not make rule-based substitute predictions.

> [!IMPORTANT]
> **Academic & Research Integrity Notice**:
> The current held-out evaluation uses a stratified random row split, which can place duplicated or temporally adjacent flows in different partitions and make results optimistic. A temporal or capture-group split is still needed for final academic claims. Prediction scores are uncalibrated model outputs, not probabilities or verified ground truth.
>
> **Current Status**: A full-data XGBoost bundle is active locally. The benchmark compares four classifiers on 2,830,743 CIC-IDS2017 flows; detailed metrics are in `reports/benchmark_metrics.json`. The bundle and raw dataset are local, git-ignored artifacts.

---

## 📑 Table of Contents

- [Executive Summary](#-executive-summary)
- [System Architecture](#-system-architecture)
- [Key Features](#-key-features)
- [Detection Models & Attack Taxonomy](#-detection-models--attack-taxonomy)
- [Security Operations Center (SOC) Frontend](#-security-operations-center-soc-frontend)
- [API Service Specification](#-api-service-specification)
- [Methodology & Leakage Prevention](#-methodology--leakage-prevention)
- [Repository Structure](#-repository-structure)
- [Installation & Setup](#-installation--setup)
- [Pipeline Execution](#-pipeline-execution)
- [Mini-Project Assessment & Rubric Alignment](#-mini-project-assessment--rubric-alignment)
- [Ethical, Privacy & Security Disclaimers](#-ethical-privacy--security-disclaimers)
- [References & Citation](#-references--citation)

---

## 🏗️ System Architecture

The implemented training and serving flow is summarized below. Current evaluation uses randomized stratified row splits; see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for its limitations and the implemented endpoints.

```mermaid
flowchart TD
    subgraph Data_Ingestion["1. Data Ingestion & Sanitization"]
        A["Raw CIC-IDS2017 CSVs\n(data/raw/cicids2017/)"] --> B["Schema Validation & Header Normalization"]
        B --> C["Data Cleaning: Inf/NaN Pruning & Column Aliasing"]
        C --> D["Clean Numeric Flow Table"]
    end

    subgraph Data_Splitting["2. Stratified Partitioning"]
        D --> E["Randomized Row Split\n(Train / Validation / Test)"]
        E --> F["Train Split (60%)"]
        E --> G["Validation Split (20%)"]
        E --> H["Frozen Test Split (20%)"]
    end

    subgraph Modeling["3. Model Training & Optimization"]
        F --> I["Feature Selection & Scaling\n(Fit on Train ONLY)"]
        I --> J["Multi-Model Benchmark:\n• Logistic Regression\n• Random Forest\n• Extra Trees\n• XGBoost"]
        G --> K["Validation Threshold Tuning\n& Metric Calibration (PR-AUC, F1)"]
        J --> K
        K --> L["Model Freezing & Packaging\n(models/<model-id>/bundle.joblib)"]
    end

    subgraph Evaluation["4. Test Set Evaluation & Reporting"]
        H --> M["Frozen Model Test Inference"]
        L --> M
        M --> N["JSON Metrics & Confusion Matrices\n(reports/benchmark_metrics.json)"]
    end

    subgraph Serving["5. Inference & Presentation Layer"]
        L --> O["FastAPI REST Backend\n(127.0.0.1:8000)"]
        O --> P["Interactive SOC Dashboard\n(React 19 + TypeScript + Tailwind 4)"]
        O --> Q["Exploratory Streamlit UI\n(Optional)"]
    end
```

---

## ✨ Planned System Capabilities

- **🛡️ Leakage-Aware Cross-Validation**: Preprocessing (imputation, scaling, encoding) is strictly fit on training data alone. Splits are partitioned across continuous temporal blocks to avoid flow-leakage across windows.
- **⚡ High-Throughput REST API**: Asynchronous endpoints engineered with **FastAPI** and **Pydantic v2** supporting single-record inspection (`/predict`), high-volume batch scoring (`/predict/batch`), and model health monitoring (`/health`).
- **🖥️ Phosphor-Green SOC Analyst Terminal**: A sleek, cyber-themed **React 19 + TypeScript** interface incorporating dark-mode aesthetics, custom bento grids, Recharts data visualizers, and Lucide telemetry icons.
- **🔍 Explainable AI (XAI)**: Integrated **SHAP (SHapley Additive exPlanations)** attribution for flow-level decision explainability, revealing which packet headers or flow durations triggered an alert.
- **📊 Multi-Class Threat Triage**: Goes beyond naive binary detection by classifying suspicious flows into structured threat families (DoS/DDoS, Port Scans, Brute Force, Web Infiltration, Botnets).
- **🔒 Privacy-Preserving Offline Operation**: Operates purely on local flow datasets. Zero packet interception, zero external telemetry calls, and strict local artifact isolation under `data/runs/`.

---

## 🎯 Detection Models & Attack Taxonomy

### Evaluated Model Architectures

| Model Class | Algorithm | Target Objective | Key Hyperparameters & Characteristics |
|---|---|---|---|
| **Linear Baseline** | Logistic Regression | Linear decision boundary baseline | L2 penalty (`C=1.0`), scaled standard features |
| **Ensemble (Bagging)** | Random Forest | Non-linear feature interactions & robustness | `n_estimators=150`, `max_depth=20`, balanced subsampling |
| **Ensemble (Boosting)** | XGBoost | SOTA gradient boosting on tabular network flows | `max_depth=6`, `learning_rate=0.08`, tree subsampling |
| **Ensemble (Extra Randomization)** | Extra Trees | Non-linear feature interactions and variance reduction | `n_estimators=160`, `max_depth=24`, balanced classes |

### Target Attack Taxonomy (CIC-IDS2017)

The system maps 14 specific attack subtypes into 5 primary operational threat families (configured in [`config/label_map.yaml`](file:///c:/Users/ishaan/OneDrive/Desktop/ML%20PROJECT/config/label_map.yaml)):

```
├── BENIGN (Normal Network Behavior)
└── MALICIOUS
    ├── DoS / DDoS (DDoS, DoS Hulk, GoldenEye, Slowloris, Slowhttptest, Heartbleed)
    ├── PortScan (Inbound Reconnaissance & Probe Traffic)
    ├── Brute Force (FTP-Patator, SSH-Patator)
    ├── Web Attacks (SQL Injection, Cross-Site Scripting [XSS], Web Brute Force)
    └── Botnet & Infiltration (Botnet ARES, Internal Privilege Escalation)
```

---

## 💻 Security Operations Center (SOC) Frontend

The user interface is an enterprise-grade cyber command center built with **React 19**, **Vite**, **TypeScript**, and **Tailwind CSS v4**, located in [`frontend/`](file:///c:/Users/ishaan/OneDrive/Desktop/ML%20PROJECT/frontend).

### Dedicated Operations Views

1. **Security Overview (`overview`)**: High-level SOC telemetry featuring key stat metrics (total flows, predicted malicious, predicted benign, operating threshold), traffic volume timeline, threat distribution donut charts, and diagnostic pipeline monitors.
2. **Threat Alerts (`alerts`)**: Triage panel displaying model-flagged flows with confidence scores, assigned severity (Low, Medium, High, Critical), protocol metadata, and one-click sanitized CSV exports.
3. **Traffic Investigation (`investigation`)**: Deep-dive forensics terminal showing individual flow packet metrics, bidirectional payload statistics, inter-arrival time (IAT), and local feature importance explanations.
4. **Network Activity (`network`)**: Protocol breakdowns (TCP/UDP/ICMP), communication port heatmaps, timeline aggregates, and talker endpoint distributions.
5. **Model Performance (`performance`)**: Cross-model table showing held-out precision, recall, F1, PR-AUC, and ROC-AUC from the generated benchmark report.
6. **Traffic Analysis Lab (`lab`)**: Local CSV upload and model scoring through the FastAPI service, with a 500 MB request limit and chunked inference.

---

## 🔌 API Service Specification

The FastAPI microservice ([`backend/`](file:///c:/Users/ishaan/OneDrive/Desktop/ML%20PROJECT/backend)) exposes low-latency endpoints for automated inference and integration:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | API and model readiness; reports `degraded` when no trusted bundle is available |
| `GET` | `/model/info` | Metadata read from the active verified model bundle; empty fields before a model exists |
| `GET` | `/model/benchmark` | Loads local train/validation/test comparison metrics for the active project |
| `POST` | `/predict` | Scores one flow when a verified model bundle is active; otherwise returns `503 model_not_loaded` |
| `POST` | `/predict/batch` | Scores 1-10,000 flow records when a verified model bundle is active |
| `POST` | `/analyze/csv` | Scores a local CSV upload in 1,000-row chunks; returns aggregate counts and up to 100 preview rows |
| `POST` | `/explain` | Returns `501 explanation_unavailable` until a supported explainer is connected |

The service never substitutes hard-coded predictions, metrics, thresholds, or explanation values when artifacts are missing. See [`backend/README.md`](backend/README.md) for its request format and local run instructions.

### Example Inference Request

```bash
curl -X POST "http://127.0.0.1:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "Destination_Port": 80,
    "Flow_Duration": 112740,
    "Total_Fwd_Packets": 3,
    "Total_Backward_Packets": 4,
    "Total_Length_of_Fwd_Packets": 161,
    "Total_Length_of_Bwd_Packets": 488,
    "Fwd_Packet_Length_Max": 161,
    "Flow_IAT_Mean": 18790.0,
    "FIN_Flag_Count": 0,
    "SYN_Flag_Count": 1
  }'
```

---

## 🔬 Methodology & Leakage Prevention

The training script keeps preprocessing fitted to training data, chooses the operating threshold on validation data, and evaluates each frozen estimator on a held-out test partition. The current implementation uses a stratified random row split, so duplicate or temporally adjacent flows may cross partitions and make test metrics optimistic. A capture-group or temporal split is needed for final academic claims.

The benchmark report is written to `reports/benchmark_metrics.json`. It compares Logistic Regression, Random Forest, Extra Trees, and XGBoost. The selected model and validation-derived threshold are packaged under `models/` with a SHA-256 checksum.

---

## 📂 Repository Structure

```text
ML-Based-NIDS/
├── .github/workflows/               # Continuous integration workflows
│   └── ci.yml                       # Python lint/test and React frontend verification
├── config/                          # Central configuration and hyperparameters
│   ├── config.yaml                  # Pipeline parameters, paths, model configs
│   └── label_map.yaml               # Attack family and severity mappings
├── data/                            # Data directory (Git-ignored)
│   ├── raw/cicids2017/              # Raw CIC-IDS2017 source CSVs
│   ├── interim/                     # Cleaned, per-file Parquet partitions
│   ├── processed/                   # Leakage-aware train/val/test splits
│   └── runs/                        # Local analyst run logs & session records
├── models/                          # Serialized model bundles & freeze checksums
├── reports/                         # Generated benchmark reports, metrics & figures
│   └── figures/                     # ROC curves, PR curves, and confusion matrices
├── notebooks/                       # Exploratory analysis and prototyping notebooks
├── src/nids/                        # Core Python NIDS package
│   ├── common/                      # Shared config, logging, paths, and custom exceptions
│   ├── data/                        # CSV inspection, cleaning, sanitation & splitting
│   ├── features/                    # Feature selection, scaling & transformers
│   ├── training/                    # Model training, hyperparameter tuning & calibration
│   ├── evaluation/                  # Classification metrics, ROC/PR, and figures
│   ├── inference/                   # Inference bundles, prediction pipeline & severity rules
│   └── storage/                     # Local run storage & optional database adapters
├── backend/                         # FastAPI application
│   ├── schemas/                     # Flow request validation
│   ├── main.py                      # App factory, health, model, predict and explain endpoints
│   ├── predictor.py                 # Verified local model bundle loading and inference adapter
│   └── README.md                    # API setup, bundle contract, and endpoint behavior
├── frontend/                        # Modern React SOC Terminal Dashboard
│   ├── src/                         # Application source (App.tsx, components, hooks)
│   │   ├── components/ui/           # Reusable UI primitives (bento grid, buttons, empty states)
│   │   └── lib/                     # Dashboard metadata, navigation, and API clients
│   ├── package.json                 # Node dependencies (React 19, Tailwind 4, Lucide, Recharts)
│   └── vite.config.ts               # Vite configuration
├── scripts/                         # Pipeline orchestration & deployment utilities
│   └── run_pipeline.py              # CLI tool for validation, cleaning, training & eval
├── tests/                           # Comprehensive test suite
│   ├── unit/                        # Data cleaning, feature transformation & metric tests
│   ├── api/                         # FastAPI route and payload validation tests
│   └── integration/                 # End-to-end pipeline verification
├── docs/                            # Academic & technical documentation
│   ├── ARCHITECTURE.md              # System architecture details
│   ├── ASSESSMENT.md                # 15-mark university rubric alignment & tracking
│   ├── DATASET.md                   # CIC-IDS2017 dataset terms, provenance & citation
│   ├── DECISIONS.md                 # Architecture Decision Records (ADRs)
│   └── PROGRESS.md                  # Implementation milestones and acceptance log
├── requirements.txt                 # Core Python production dependencies
├── requirements-dev.txt             # Testing and linting tooling (pytest, ruff, black)
└── pyproject.toml                   # Standard Python project packaging specification
```

---

## 🚀 Installation & Setup

### Prerequisites

- **Python**: 3.10, 3.11, or 3.12 (Python 3.11 recommended)
- **Node.js**: v20.19+ or v22.12+ (for the React Frontend)
- **RAM**: Minimum 8 GB (16 GB recommended for full dataset training)
- **Disk Space**: ~10 GB free space recommended for Parquet caching

---

### 1. Python Environment Setup

#### Windows (PowerShell)
```powershell
# Create and activate virtual environment
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

#### Linux / macOS
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

---

### 2. Frontend Setup (React SOC Dashboard)

```bash
cd frontend
npm install
npm run dev
```
The dashboard will be accessible at `http://localhost:5173`.

---

### 3. Dataset Acquisition

1. Download the official **CIC-IDS2017** CSV archive from the [Canadian Institute for Cybersecurity (UNB)](https://www.unb.ca/cic/datasets/ids-2017.html).
2. Extract the CSV files directly into the raw data directory:
   ```text
   data/raw/cicids2017/
   ├── Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv
   ├── Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv
   ├── Friday-WorkingHours-Morning.pcap_ISCX.csv
   └── ...
   ```
*(Note: Raw dataset files are ignored by git to protect repository size and license terms).*

---

## ⚙️ Pipeline Execution

Install dependencies, place the official CIC-IDS2017 CSV files in `data/raw/cicids2017/`, then train and package the model:

```powershell
# Quick smoke run on a reproducible 5% sample of each CSV
python scripts/run_pipeline.py --fast

# Full run; trains four classifiers and writes a verified model bundle
python scripts/run_pipeline.py

# Metrics for each model are written to reports/benchmark_metrics.json.
# Bundle is written below models/ and its ID recorded in models/ACTIVE.

# Start or restart the API after training so it loads the active bundle
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

The current split is stratified and randomized at the row level; for final academic results, use a time- or capture-group-aware split to reduce the chance of related flows appearing across partitions. The fast sample is for a smoke run only and must not be reported as final performance.

---

## 🎓 Mini-Project Assessment & Rubric Alignment

This repository is structured around the **15-Mark Mini-Project Rubric** and the **10-Page Research Report**:

| Area | Marks | Implementation & Repository Evidence |
|---|:---:|---|
| **Data Cleaning & Splitting** | **3** | CSV header normalization, nonnumeric and infinite value handling, stratified train/validation/test partitioning, and preprocessing fitted on training data. |
| **Model Comparison & Analytics** | **4** | Logistic Regression, Random Forest, Extra Trees, and XGBoost comparison with precision, recall, F1, PR-AUC, ROC-AUC, and confusion matrices in `reports/benchmark_metrics.json`. |
| **UI Deployment & Accessibility** | **4** | Enterprise React 19 SOC terminal dashboard (`frontend/`), cross-platform responsive layout, offline file upload lab, and optional Streamlit explorer. |
| **Code Quality & Documentation** | **4** | Clean modular architecture, Ruff/Black code standards, unit & API test suites (`tests/`), complete architecture records, and academic report alignment. |

> Detailed progress tracking, milestones, and report templates are maintained in [`docs/ASSESSMENT.md`](file:///c:/Users/ishaan/OneDrive/Desktop/ML%20PROJECT/docs/ASSESSMENT.md).

---

## ⚖️ Ethical, Privacy & Security Disclaimers

1. **Offline Scope Only**: This software is built for forensic and retrospective network-flow analysis. It does **not** capture raw network interfaces, promiscuously listen to sockets, sniff live packets, or monitor third-party communications.
2. **Privacy by Design**: All analyses execute locally on the analyst's machine. Flow records and IP addresses are not transmitted to external telemetry services or cloud vendors.
3. **Statistical Outputs**: Predictions represent probabilistic model inferences derived from 2017 simulated synthetic lab environments. They must serve as triage aids for human security analysts, not autonomous incident triggers.

---

## 📚 References & Citation

If you use this codebase or project scaffold in your research or coursework, please cite the underlying CIC-IDS2017 dataset:

```bibtex
@inproceedings{sharafaldin2018toward,
  title={Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization},
  author={Sharafaldin, Iman and Lashkari, Arash Habibi and Ghorbani, Ali A.},
  booktitle={Proceedings of the 4th International Conference on Information Systems Security and Privacy (ICISSP)},
  pages={108--116},
  year={2018},
  organization={SCITEPRESS}
}
```

---

<p align="center">
  <sub>Built for advanced machine learning research and modern security operations.</sub>
</p>
