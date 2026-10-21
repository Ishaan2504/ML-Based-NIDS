"""Measure the active NSL-KDD model on the official held-out KDDTest+ split."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from backend.nsl_kdd_predictor import KDD_COLUMNS, KDD_FEATURES, NslKddPredictor


def evaluate(test_path: Path, model_path: Path, output_path: Path) -> dict[str, object]:
    frame = pd.read_csv(
        test_path,
        names=KDD_COLUMNS,
        header=None,
        skipinitialspace=True,
    )
    frame["label"] = frame["label"].astype(str).str.strip().str.rstrip(".").str.lower()
    predictor = NslKddPredictor.from_path(model_path)
    predictions = predictor.predict_many(frame[KDD_FEATURES].to_dict(orient="records"))
    predicted_labels = [item["predicted_label"] for item in predictions]
    actual_labels = frame["label"].tolist()
    supported_labels = sorted(str(label).strip().lower() for label in predictor.label_encoder.classes_)
    supported_mask = frame["label"].isin(supported_labels)
    supported_rows = int(supported_mask.sum())
    supported_correct = sum(
        actual == predicted
        for actual, predicted, supported in zip(actual_labels, predicted_labels, supported_mask)
        if supported
    )
    all_correct = sum(actual == predicted for actual, predicted in zip(actual_labels, predicted_labels))

    result: dict[str, object] = {
        "model_id": predictor.model_id,
        "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "dataset": "NSL-KDD KDDTest+",
        "dataset_reference": "https://www.unb.ca/cic/datasets/nsl.html",
        "accuracy": supported_correct / supported_rows if supported_rows else None,
        "accuracy_scope": "Rows whose ground-truth label is one of the model's supported classes",
        "test_rows": supported_rows,
        "correct_rows": supported_correct,
        "full_test_accuracy": all_correct / len(frame) if len(frame) else None,
        "full_test_rows": len(frame),
        "full_test_correct_rows": all_correct,
        "excluded_out_of_scope_rows": len(frame) - supported_rows,
        "supported_labels": supported_labels,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test", type=Path, default=Path("data/raw/nsl_kdd/KDDTest+.txt"))
    parser.add_argument("--model", type=Path, default=Path("models/ml_ctd/xgboost_model.pkl"))
    parser.add_argument("--output", type=Path, default=Path("reports/nsl_kdd_test_metrics.json"))
    args = parser.parse_args()
    result = evaluate(args.test, args.model, args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
