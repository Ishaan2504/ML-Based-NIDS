# GitHub Actions status

The latest observed workflow was CI Pipeline #6 on commit `5c92682` (2026-10-19). The React frontend job passed. The Python job failed in `ruff check .`, so pytest did not run in that workflow. Local checks after the fixes pass: Ruff, all 13 pytest tests, and the frontend production build.

Remaining trailing whitespace in Python files, including `verify_ci_ready.py`, has been removed. FastAPI and HTTPX ranges are constrained to versions compatible with the synchronous test client.

No raw CIC-IDS2017 CSV files are present in `data/raw/cicids2017/`. Per the technical specification, the validation stage now stops with exit code 2 and an actionable request for those files. Processing, training, and evaluation stages report that they are not implemented instead of claiming to create artifacts.
