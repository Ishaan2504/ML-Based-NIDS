#!/usr/bin/env python3
"""Train and package a binary CIC-IDS2017 flow classifier for the local API."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parents[1]
SEED = 42


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data/raw/cicids2017",
                        help="Directory containing CIC-IDS2017 CSV files")
    parser.add_argument("--models-dir", type=Path, default=ROOT / "models")
    parser.add_argument("--reports-dir", type=Path, default=ROOT / "reports")
    parser.add_argument("--fast", action="store_true",
                        help="Use a reproducible 5%% row sample from each CSV for a quick demo")
    parser.add_argument("--sample-frac", type=float, default=0.05,
                        help="Fraction of rows sampled per CSV when --fast is used")
    return parser.parse_args()


def normalize_column(name: Any) -> str:
    return re.sub(r"\s+", " ", str(name).replace("\ufeff", "")).strip()


def load_data(data_dir: Path, fast: bool, sample_frac: float) -> pd.DataFrame:
    files = sorted(data_dir.glob("*.csv"))
    if not files:
        raise FileNotFoundError(
            f"No CSV files found in {data_dir}. Download CIC-IDS2017 flow CSVs and put them there."
        )
    frames = []
    for path in files:
        print(f"Reading {path.name}...")
        frame = pd.read_csv(path, low_memory=False, encoding="cp1252", encoding_errors="replace")
        frame.columns = [normalize_column(c) for c in frame.columns]
        frame = frame.loc[:, ~frame.columns.duplicated()]
        label_col = next((c for c in frame.columns if c.lower() == "label"), None)
        if label_col is None:
            raise ValueError(f"No Label column found in {path.name}")
        if fast:
            frame = frame.sample(frac=sample_frac, random_state=SEED)
        frames.append(frame)
    data = pd.concat(frames, ignore_index=True)
    label_col = next(c for c in data.columns if c.lower() == "label")
    data[label_col] = data[label_col].astype("string").str.strip()
    data = data.dropna(subset=[label_col])
    data = data[data[label_col] != ""]
    data["target"] = (data[label_col].str.upper() != "BENIGN").astype("int8")
    # Original label and obvious row identifiers are excluded from model inputs.
    drop_columns = {label_col, "target"}
    identifier_names = {"flow id", "source ip", "destination ip", "timestamp"}
    drop_columns.update(c for c in data.columns if c.lower() in identifier_names)
    features = data.drop(columns=list(drop_columns), errors="ignore")
    for column in features.columns:
        features[column] = pd.to_numeric(features[column], errors="coerce")
    features = features.replace([np.inf, -np.inf], np.nan)
    usable = features.notna().any(axis=0)
    features = features.loc[:, usable]
    if features.shape[1] == 0:
        raise ValueError("No numeric feature columns remain after cleaning.")
    cleaned = features.copy()
    cleaned["target"] = data["target"].to_numpy()
    cleaned = cleaned.dropna(subset=["target"])
    if cleaned["target"].nunique() != 2:
        raise ValueError("The input data must include both BENIGN and attack rows.")
    return cleaned


def build_models() -> dict[str, Pipeline]:
    return {
        "Logistic Regression": Pipeline([
            ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("scale", StandardScaler()),
            ("model", LogisticRegression(max_iter=1000, class_weight="balanced", n_jobs=-1,
                                          random_state=SEED)),
        ]),
        "Random Forest": Pipeline([
            ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("model", RandomForestClassifier(n_estimators=160, max_depth=24,
                min_samples_leaf=2, class_weight="balanced_subsample", n_jobs=-1,
                random_state=SEED)),
        ]),
        "Extra Trees": Pipeline([
            ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("model", ExtraTreesClassifier(n_estimators=160, max_depth=24,
                min_samples_leaf=2, class_weight="balanced", n_jobs=-1,
                random_state=SEED)),
        ]),
        "XGBoost": Pipeline([
            ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("model", XGBClassifier(n_estimators=160, max_depth=6, learning_rate=0.08,
                subsample=0.8, colsample_bytree=0.8, tree_method="hist",
                eval_metric="logloss", n_jobs=-1, random_state=SEED)),
        ]),
    }


def positive_scores(model: Pipeline, x: pd.DataFrame) -> np.ndarray:
    return np.asarray(model.predict_proba(x))[:, 1]


def choose_threshold(y: pd.Series, scores: np.ndarray) -> float:
    thresholds = np.unique(np.quantile(scores, np.linspace(0.05, 0.95, 181)))
    return float(max(thresholds, key=lambda t: f1_score(y, scores >= t, zero_division=0)))


def metrics(y: pd.Series, scores: np.ndarray, threshold: float) -> dict[str, Any]:
    pred = scores >= threshold
    return {
        "threshold": float(threshold),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "pr_auc": float(average_precision_score(y, scores)),
        "roc_auc": float(roc_auc_score(y, scores)),
        "confusion_matrix": confusion_matrix(y, pred, labels=[0, 1]).tolist(),
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def installed_version(package: str) -> str | None:
    try:
        return version(package)
    except PackageNotFoundError:
        return None


def train(args: argparse.Namespace) -> None:
    if not 0 < args.sample_frac <= 1:
        raise ValueError("--sample-frac must be greater than 0 and at most 1")
    data = load_data(args.data_dir, args.fast, args.sample_frac)
    y = data.pop("target").astype("int8")
    x_train, x_holdout, y_train, y_holdout = train_test_split(
        data, y, test_size=0.4, random_state=SEED, stratify=y
    )
    x_val, x_test, y_val, y_test = train_test_split(
        x_holdout, y_holdout, test_size=0.5, random_state=SEED, stratify=y_holdout
    )
    print(f"Clean flows: {len(data):,}; features: {len(data.columns)}")
    print(f"Split sizes: train={len(x_train):,}, validation={len(x_val):,}, test={len(x_test):,}")

    results: dict[str, Any] = {}
    fitted: dict[str, Pipeline] = {}
    for name, model in build_models().items():
        print(f"Training {name}...")
        model.fit(x_train, y_train)
        val_scores = positive_scores(model, x_val)
        threshold = choose_threshold(y_val, val_scores)
        results[name] = {"validation": metrics(y_val, val_scores, threshold),
                         "test": metrics(y_test, positive_scores(model, x_test), threshold)}
        fitted[name] = model
        print(f"  validation F1={results[name]['validation']['f1']:.4f}; "
              f"test F1={results[name]['test']['f1']:.4f}")

    winner = max(results, key=lambda name: results[name]["validation"]["pr_auc"])
    selected = fitted[winner]
    threshold = results[winner]["validation"]["threshold"]
    created = datetime.now(timezone.utc).isoformat()
    model_id = "cicids2017-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    args.models_dir.mkdir(parents=True, exist_ok=True)
    bundle_dir = args.models_dir / model_id
    bundle_dir.mkdir()
    # Keep the train-fitted estimator: threshold calibration and test evaluation
    # remain on independent partitions and the deployed score scale is unchanged.
    bundle = {
        "schema_version": 1,
        "binary_pipeline": selected,
        "feature_names": list(data.columns),
        "threshold": threshold,
        "threshold_policy": "validation_f1_maximization",
        "score_type": "attack_score",
        "created_at": created,
        "model_name": winner,
        "library_versions": {name: installed_version(name)
                             for name in ("scikit-learn", "xgboost", "numpy", "pandas")},
        "family_classes": [],
        "feature_ranges": {c: {"min": float(data[c].min()), "max": float(data[c].max())}
                           for c in data.columns if data[c].notna().any()},
        "dataset_info": {"name": "CIC-IDS2017", "rows": int(len(data)),
                         "train_rows": int(len(x_train)), "validation_rows": int(len(x_val)),
                         "test_rows": int(len(x_test)), "fast_sample": bool(args.fast)},
        "metrics_refs": {"report": "reports/benchmark_metrics.json"},
    }
    joblib.dump(bundle, bundle_dir / "bundle.joblib", compress=3)
    (bundle_dir / "bundle.sha256").write_text(sha256(bundle_dir / "bundle.joblib") + "\n",
                                                encoding="ascii")
    meta = {"schema_version": 1, "model_id": model_id, "model_name": winner,
            "created_at": created, "dataset": "CIC-IDS2017", "threshold": threshold}
    (bundle_dir / "bundle_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    (args.models_dir / "ACTIVE").write_text(model_id + "\n", encoding="utf-8")
    args.reports_dir.mkdir(parents=True, exist_ok=True)
    report = {"dataset": "CIC-IDS2017", "rows": int(len(data)), "features": list(data.columns),
              "selected_model": winner, "selection_metric": "validation PR-AUC",
              "models": results, "test_set_used_for_selection": False}
    (args.reports_dir / "benchmark_metrics.json").write_text(json.dumps(report, indent=2) + "\n",
                                                              encoding="utf-8")
    print(f"\nActive model: {winner} ({model_id})")
    print(f"Bundle: {bundle_dir}")
    print(f"Metrics: {args.reports_dir / 'benchmark_metrics.json'}")
    print("Restart the API so it loads the new active model.")


def main() -> int:
    args = parse_args()
    try:
        train(args)
        return 0
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
