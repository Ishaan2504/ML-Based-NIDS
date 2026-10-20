# Mini-Project Assessment & Rubric Alignment

This document tracks the formal academic evaluation rubric and delivery milestones for the ML-Based Network Intrusion Detection System mini-project.

## 15-Mark University Rubric Breakdown

| Area | Marks | Criteria & Requirements | Project Implementation & Evidence |
|---|:---:|---|---|
| **Data Cleaning & Splitting** | **3** | • Inspect raw flow files<br>• Handle corrupt, infinite (`Inf`), and missing values<br>• Normalize headers and exclude identifiers/target leakage<br>• Use a leakage-aware train/validation/test split | Implemented in `scripts/run_pipeline.py`; the current split is stratified random by row, so temporal/group leakage is still possible. A capture-group or temporal split remains required for the full criterion. |
| **Model Comparison & Analytics** | **4** | • Benchmark at least **4 distinct ML models**<br>• Report precision, recall, F1, PR-AUC, ROC-AUC, and confusion matrices<br>• Include FAR and feature explanations in final analysis | Full CIC-IDS2017 comparison for Logistic Regression, Random Forest, Extra Trees, and XGBoost is in `reports/benchmark_metrics.json`. Figures, FAR, and SHAP explanations remain to be added. |
| **UI Deployment & Cross-Platform Accessibility** | **4** | • Interactive UI<br>• Offline batch analysis<br>• Setup documentation<br>• Verify responsive, accessible use across operating systems | React dashboard, API status, CSV upload/inference, and benchmark view run locally. Cross-platform accessibility and responsive testing remain to be documented. Alerts, Investigation, and Network views remain scaffolds. |
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
- [x] React dashboard connected to the local API for CSV scoring and benchmark metrics
- [x] Architectural documentation and Decision Records (ADRs) authored
- [x] CIC-IDS2017 dataset taxonomy and capture schedule documented
- [x] Configuration schemas (labels, features, hyperparameters) defined
- [x] Data cleaning, validation threshold selection, and held-out test evaluation executed
- [ ] Temporal/capture-group partitioning implemented and verified
- [ ] Figures, false-alarm rate, and feature-explanation analysis generated
- [ ] Literature review draft comparing 5 recent papers completed
- [ ] Final 10-page academic report compiled
