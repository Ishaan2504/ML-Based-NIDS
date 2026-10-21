"""Train the NSL-KDD XGBoost model used by the FastAPI inference service."""

from __future__ import annotations

import argparse
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.preprocessing import LabelEncoder, StandardScaler
from xgboost import XGBClassifier

KDD_COLUMNS = [
    "duration", "protocol_type", "service", "flag", "src_bytes", "dst_bytes",
    "land", "wrong_fragment", "urgent", "hot", "num_failed_logins", "logged_in",
    "num_compromised", "root_shell", "su_attempted", "num_root", "num_file_creations",
    "num_shells", "num_access_files", "num_outbound_cmds", "is_host_login",
    "is_guest_login", "count", "srv_count", "serror_rate", "srv_serror_rate",
    "rerror_rate", "srv_rerror_rate", "same_srv_rate", "diff_srv_rate",
    "srv_diff_host_rate", "dst_host_count", "dst_host_srv_count",
    "dst_host_same_srv_rate", "dst_host_diff_srv_rate", "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate", "dst_host_serror_rate", "dst_host_srv_serror_rate",
    "dst_host_rerror_rate", "dst_host_srv_rerror_rate", "label", "difficulty",
]
CATEGORICAL_FEATURES = ["protocol_type", "service", "flag"]


def _load(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, names=KDD_COLUMNS, header=None, skipinitialspace=True)
    frame["label"] = frame["label"].astype(str).str.strip().str.rstrip(".").str.lower()
    # Keep every attack type represented in KDDTrain+. The held-out KDDTest+ split
    # is evaluated separately and is never used during training.
    return frame.drop_duplicates().copy()


def train(train_path: Path, output_path: Path) -> None:
    train_frame = _load(train_path)
    if train_frame.empty:
        raise ValueError("The training file contains no rows.")

    # Drop columns constant in training, matching the selected upstream model's schema.
    constant = [column for column in train_frame if train_frame[column].nunique(dropna=False) <= 1]
    train_frame = train_frame.drop(columns=constant)
    X_train = train_frame.drop(columns=["label", "difficulty"], errors="ignore")
    y_train = train_frame["label"]

    numeric_features = [
        column for column in X_train.columns if column not in CATEGORICAL_FEATURES
    ]
    feature_encoders: dict[str, LabelEncoder] = {}
    for column in CATEGORICAL_FEATURES:
        encoder = LabelEncoder()
        X_train[column] = encoder.fit_transform(X_train[column].astype(str).str.strip().str.lower())
        feature_encoders[column] = encoder

    scaler = StandardScaler()
    scaled_numeric = scaler.fit_transform(X_train[numeric_features].astype(float))
    for position, feature in enumerate(numeric_features):
        X_train[feature] = scaled_numeric[:, position]

    target_encoder = LabelEncoder()
    y_encoded = target_encoder.fit_transform(y_train)
    feature_encoders["target_encoder"] = target_encoder

    selector = SelectKBest(score_func=f_classif, k=min(30, X_train.shape[1]))
    selected = selector.fit_transform(X_train, y_encoded)
    selected_features = [
        name for name, keep in zip(X_train.columns, selector.get_support()) if keep
    ]

    model = XGBClassifier(
        n_estimators=200,
        max_depth=30,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        min_child_weight=2,
        gamma=0.15,
        reg_alpha=0.3,
        objective="multi:softprob",
        num_class=len(target_encoder.classes_),
        random_state=42,
        n_jobs=-1,
        eval_metric="mlogloss",
    )
    model.fit(selected, y_encoded)
    label_mapping = {int(value): int(value) for value in np.unique(y_encoded)}
    reverse_label_mapping = {mapped: original for original, mapped in label_mapping.items()}

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    artifact = {
        "model": model,
        "label_encoders": feature_encoders,
        "scaler": scaler,
        "selected_features_scaler": None,
        "feature_names": selected_features,
        "label_mapping": label_mapping,
        "reverse_label_mapping": reverse_label_mapping,
        "selected_labels": target_encoder.classes_.tolist(),
    }
    with temporary_path.open("wb") as stream:
        pickle.dump(artifact, stream, protocol=pickle.HIGHEST_PROTOCOL)
    temporary_path.replace(output_path)
    print(
        f"Saved NSL-KDD XGBoost model to {output_path} "
        f"({len(train_frame):,} training rows, {len(selected_features)} selected features)."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, default=Path("data/raw/nsl_kdd/KDDTrain+.txt"))
    parser.add_argument(
        "--output", type=Path, default=Path("models/ml_ctd/xgboost_model.pkl")
    )
    args = parser.parse_args()
    train(args.train, args.output)


if __name__ == "__main__":
    main()
