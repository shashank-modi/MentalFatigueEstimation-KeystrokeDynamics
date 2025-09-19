# Glue: pick latest NDJSON -> window -> compute -> postprocess -> save CSV
import os
from datetime import datetime, timezone
import pandas as pd

from src.features.windowing import latest_raw_file, read_ndjson, add_window_index
from src.features.computecore import compute_window_features
from src.features.postprocess import fill_and_clip

WINDOW_MS = 60_000
FEATURES_DIR = "data/features"

def iso_stamp():
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%dT%H-%M-%S")

def main():
    raw_path = latest_raw_file("data/raw")
    print(f"[features] Using raw: {raw_path}")

    df = read_ndjson(raw_path)
    if df.empty:
        print("[features] Raw file is empty. Collect more events and rerun.")
        return

    df = add_window_index(df, window_ms=WINDOW_MS)
    feats = compute_window_features(df)
    feats = fill_and_clip(feats)

    os.makedirs(FEATURES_DIR, exist_ok=True)
    out_csv = os.path.join(FEATURES_DIR, f"features_{iso_stamp()}.csv")
    feats.to_csv(out_csv, index=False)
    print(f"[features] Wrote {len(feats)} rows -> {out_csv}")

if __name__ == "__main__":
    main()