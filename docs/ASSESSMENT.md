# Mini-Project Assessment & Rubric Alignment

This document tracks the formal academic evaluation rubric and delivery milestones for the ML-Based Network Intrusion Detection System mini-project.

## 15-Mark University Rubric Breakdown

| Area | Marks | Criteria & Requirements | Project Implementation & Evidence |
|---|:---:|---|---|
| **Data Cleaning & Splitting** | **3** | • Documented inspection of raw flow files<br>• Removal of corrupt rows, infinite values (`Inf`), and `NaN`s<br>• Normalization of headers and column aliasing<br>• **Leakage-aware train/val/test splits** (preventing temporal shortcut bias) | Handled in `src/nids/data/clean.py` and `src/nids/data/split.py`. Contiguous block partitioning ensures zero bleed between partitions. |
| **Model Comparison & Analytics** | **4** | • Benchmarking of at least **4 distinct ML models**<br>• Quantitative performance metrics (Accuracy, Precision, Recall, F1, PR-AUC, ROC-AUC)<br>• Transparent reporting of confusion matrices and False Alarm Rates (FAR)<br>• SHAP feature importance explanations | Benchmarked architectures: Logistic Regression, Random Forest, XGBoost, and Isolation Forest. Artifacts stored in `reports/` with figures. |
| **UI Deployment & Cross-Platform Accessibility** | **4** | • Modern, interactive user interface<br>• Real-time or batch offline analysis capability<br>• Clear setup and execution documentation<br>• Responsive, accessible design across operating systems | React 19 + TypeScript + Tailwind 4 terminal-themed SOC console (`frontend/`) with 6 dedicated views, plus optional Streamlit dashboard. |
| **Code Quality, Repository & Report** | **4** | • Clean, modular, and PEP8/Ruff compliant codebase<br>• Proper git version control with atomic commits<br>• Clear documentation (`README.md`, `ARCHITECTURE.md`, `DECISIONS.md`)<br>• Comprehensive 10-page academic report adhering to required structure | Fully structured repository with tests, central YAML configurations, GitHub Actions CI workflow, and report outline. |

## 10-Page Research Report Outline

The final mini-project submission conforms to the following 8-section academic report structure:

1. **Introduction**: Problem statement, challenges in network intrusion detection, and project scope.
2. **Literature Review**: Critical analysis and comparative table of at least 5 recent peer-reviewed papers on ML-based NIDS.
3. **Methodology**: System architecture, threat modeling, and defense-in-depth principles.
4. **Data Cleaning & Preprocessing**: CIC-IDS2017 characteristics, feature extraction, cleaning strategies, and anti-leakage splitting.
5. **Results & Discussion**: Empirical validation results, operating threshold selection, and error analysis.
6. **State-of-the-Art Models Comparison**: Cross-model benchmark table comparing 4 algorithms across precision, recall, F1, and latency.
7. **User Interface Development & Deployment**: Architecture of the React SOC console, REST API endpoints, and analyst workflow.
8. **References**: Academic bibliography including CIC-IDS2017 dataset citations.

## Milestone Checklist

- [x] Repository scaffold, modular package structure, and dependencies configured
- [x] React 19 SOC terminal dashboard implemented with bento grid and telemetry views
- [x] Architectural documentation and Decision Records (ADRs) authored
- [x] CIC-IDS2017 dataset taxonomy and capture schedule documented
- [x] Configuration schemas (labels, features, hyperparameters) defined
- [ ] Pipeline data cleaning and leakage-aware partitioning verified
- [ ] Model training, validation threshold tuning, and frozen test evaluation executed
- [ ] Literature review draft comparing 5 recent papers completed
- [ ] Final 10-page academic report compiled
