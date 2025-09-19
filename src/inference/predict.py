# Loads the newest model and predicts on the latest features CSV's last row.
import os, json, glob
import pandas as pd
import joblib

FEATURES_DIR = "data/features"
MODELS_DIR   = "models"

def latest(path_glob: str) -> str:
    files = sorted(glob.glob(path_glob))
    if not files:
        raise FileNotFoundError(f"No matches for {path_glob}")
    return files[-1]

def load_latest_model():
    model_dir = latest(os.path.join(MODELS_DIR, "*_rf"))
    model = joblib.load(os.path.join(model_dir, "model.joblib"))
    with open(os.path.join(model_dir, "features_used.json"), "r") as f:
        feats = json.load(f)
    return model, feats, model_dir

def main():
    features_csv = latest(os.path.join(FEATURES_DIR, "features_*.csv"))
    print(f"[predict] Using features: {features_csv}")

    df = pd.read_csv(features_csv)
    if df.empty:
        raise ValueError("Features file is empty.")
    last = df.iloc[-1:].copy()

    model, feature_cols, model_dir = load_latest_model()
    # Align columns exactly as during training
    X = last[feature_cols]

    score = float(model.predict(X)[0])
    print(f"[predict] Model: {model_dir}")
    print(f"[predict] Window_id={int(last['window_id'].iloc[0])} → Fatigue score ≈ {score:.2f}")

if __name__ == "__main__":
    main()