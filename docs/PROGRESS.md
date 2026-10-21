# Project Implementation Progress

## Completed

- React dashboard and FastAPI service are connected for local offline CSV analysis.
- The API loads the NSL-KDD XGBoost model and exposes health, model metadata, single-flow, batch, and CSV inference endpoints.
- `/analyze/csv` processes NSL-KDD uploads in 1,000-row chunks and returns aggregate predictions with a 100-row preview.
- The dashboard provides API readiness, latest analysis counts, and CSV upload.
- CIC-IDS2017 CSV data was downloaded to the git-ignored `data/raw/cicids2017/` directory.
- Full-data training ran on 2,830,743 rows and 78 numeric features with stratified 60/20/20 train/validation/test partitions.
- Logistic Regression, Random Forest, Extra Trees, and XGBoost were compared. XGBoost was selected by validation PR-AUC.
- The active API model is `models/ml_ctd/xgboost_model.pkl`; the separate CIC-IDS2017 research pipeline remains independent.
- The React app and API were previously smoke-tested with the NSL-KDD synthetic upload sample.

## Limitations

- Partitions are randomized by row, not grouped by capture or time. Repeated and adjacent flows can cross partitions, which can inflate metrics. Use a temporal or capture-group split before making final academic performance claims.
- The current UI does not persist analysis runs, and it does not provide benchmark charts or feature explanations for the NSL-KDD model.
- The generated benchmark contains JSON metrics and confusion matrices; ROC/PR figures are not generated yet.
- Raw dataset files remain git-ignored. The active NSL-KDD model artifact is available at `models/ml_ctd/xgboost_model.pkl`.
