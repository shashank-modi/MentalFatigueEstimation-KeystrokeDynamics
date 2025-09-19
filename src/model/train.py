# Trains a quick baseline (RandomForestRegressor) and saves artifacts.
import os, json
from datetime import datetime, timezone

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
import joblib

DATASET_CSV = "data/datasets/train.csv"
MODELS_DIR  = "models"

EXCLUDE = {"window_id", "t_start", "t_end", "fatigue_score"}

def iso_stamp():
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%dT%H-%M-%S")

def main():
    if not os.path.exists(DATASET_CSV):
        raise FileNotFoundError(f"{DATASET_CSV} not found. Build it first.")

    df = pd.read_csv(DATASET_CSV)
    if "fatigue_score" not in df.columns:
        raise ValueError("train.csv must have a fatigue_score column.")

    # Feature order = all numeric columns except the excluded + label
    feature_cols = [c for c in df.columns if c not in EXCLUDE]
    X = df[feature_cols]
    y = df["fatigue_score"]

    # Handle tiny datasets gracefully
    if len(df) >= 10:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False  # time-aware-ish: keep order
        )
    else:
        # With very few rows, just train on all and evaluate on the same (not ideal, OK for demo)
        X_train, y_train = X, y
        X_test,  y_test  = X, y

    model = RandomForestRegressor(
        n_estimators=300, random_state=42, n_jobs=-1
    )
    model.fit(X_train, y_train)

    y_hat = model.predict(X_test)
    mae = float(mean_absolute_error(y_test, y_hat))

    # Save artifacts
    os.makedirs(MODELS_DIR, exist_ok=True)
    out_dir = os.path.join(MODELS_DIR, f"{iso_stamp()}_rf")
    os.makedirs(out_dir, exist_ok=True)

    joblib.dump(model, os.path.join(out_dir, "model.joblib"))

    with open(os.path.join(out_dir, "features_used.json"), "w") as f:
        json.dump(feature_cols, f, indent=2)

    with open(os.path.join(out_dir, "metrics.json"), "w") as f:
        json.dump(
            {"rows": len(df), "mae": mae, "note": "Tiny data → MAE may be optimistic"},
            f,
            indent=2,
        )

    print(f"[train] Saved model to {out_dir}")
    print(f"[train] Test MAE: {mae:.3f}")
    print(f"[train] Features used ({len(feature_cols)}): {feature_cols}")

if __name__ == "__main__":
    main()