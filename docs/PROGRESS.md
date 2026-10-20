# Project Implementation Progress

## Completed

- React dashboard and FastAPI service are connected for local offline CSV analysis.
- The API verifies the active model bundle checksum before loading it.
- `/analyze/csv` processes uploaded flow CSVs in 1,000-row chunks and returns aggregate predictions with a 100-row preview.
- `/model/benchmark` serves the generated four-model comparison report to the Model Performance view.
- CIC-IDS2017 CSV data was downloaded to the git-ignored `data/raw/cicids2017/` directory.
- Full-data training ran on 2,830,743 rows and 78 numeric features with stratified 60/20/20 train/validation/test partitions.
- Logistic Regression, Random Forest, Extra Trees, and XGBoost were compared. XGBoost was selected by validation PR-AUC.
- The checksummed active bundle is in `models/`; test metrics are in `reports/benchmark_metrics.json`.
- `npm run build` passed. The API was exercised with a 1,005-row CIC sample across the chunk boundary and with the schema-compatible synthetic upload sample.

## Limitations

- Partitions are randomized by row, not grouped by capture or time. Repeated and adjacent flows can cross partitions, which can inflate metrics. Use a temporal or capture-group split before making final academic performance claims.
- The current classifier is binary. The optional multiclass-family pipeline, SHAP explanations, persistent analysis runs, and the Alerts, Investigation, and Network views are not implemented.
- The generated benchmark contains JSON metrics and confusion matrices; ROC/PR figures are not generated yet.
- Raw dataset files and trained model binaries are git-ignored and have not been pushed to GitHub.
