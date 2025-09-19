# src/features/dataset_builder.py
# Join latest features with timestamp-range labels into a supervised dataset.

import os
import pandas as pd

FEATURES_DIR = "data/features"
LABELS_CSV   = "data/labels/labels.csv"
DATASETS_DIR = "data/datasets"

def _latest_features_path() -> str:
    files = sorted([os.path.join(FEATURES_DIR, f)
                    for f in os.listdir(FEATURES_DIR)
                    if f.startswith("features_") and f.endswith(".csv")])
    if not files:
        raise FileNotFoundError(f"No features CSVs found in {FEATURES_DIR}. Run make_features first.")
    return files[-1]

def _load_features() -> pd.DataFrame:
    path = _latest_features_path()
    feats = pd.read_csv(path)
    required = {"window_id", "t_start", "t_end"}
    missing = required - set(feats.columns)
    if missing:
        raise ValueError(f"Features file missing columns: {missing}")
    return feats

def _load_labels() -> pd.DataFrame:
    if not os.path.exists(LABELS_CSV):
        raise FileNotFoundError(f"{LABELS_CSV} not found. Collect labels with the GUI scheduler first.")
    labels = pd.read_csv(LABELS_CSV)
    need = {"applies_from", "applies_to", "fatigue_score"}
    if not need.issubset(labels.columns):
        raise ValueError(f"labels.csv must have columns: {need}")
    # ensure ints/floats
    labels["applies_from"] = labels["applies_from"].astype("int64")
    labels["applies_to"]   = labels["applies_to"].astype("int64")
    labels["fatigue_score"] = labels["fatigue_score"].astype(float)
    return labels

def _overlap(a_start, a_end, b_start, b_end) -> bool:
    return not (a_end < b_start or a_start > b_end)

def _map_labels_to_windows(feats: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    """
    For each window, find labels whose [applies_from, applies_to] overlaps [t_start, t_end].
    If multiple labels overlap a window, take the one with the most recent applies_to (last known state).
    Returns a DataFrame with columns: window_id, fatigue_score
    """
    rows = []
    labels_sorted = labels.sort_values("applies_to")

    for _, w in feats[["window_id","t_start","t_end"]].iterrows():
        wid, ws, we = int(w["window_id"]), int(w["t_start"]), int(w["t_end"])
        # find overlapping labels
        mask = (labels_sorted["applies_to"] >= ws) & (labels_sorted["applies_from"] <= we)
        overlaps = labels_sorted.loc[mask]
        if overlaps.empty:
            continue
        chosen = overlaps.iloc[-1]
        rows.append({"window_id": wid, "fatigue_score": float(chosen["fatigue_score"])})

    if not rows:
        raise ValueError("No windows overlapped any label ranges. Collect more labels or re-run features.")

    return pd.DataFrame(rows)

def build_dataset():
    feats = _load_features()
    labels = _load_labels()
    mapping = _map_labels_to_windows(feats, labels)
    # inner join keeps only labeled windows (good for supervised training)
    df = feats.merge(mapping, on="window_id", how="inner")
    os.makedirs(DATASETS_DIR, exist_ok=True)
    out_csv = os.path.join(DATASETS_DIR, "train.csv")
    df.to_csv(out_csv, index=False)
    print(f"[dataset] Built training dataset with {len(df)} labeled rows → {out_csv}")

if __name__ == "__main__":
    build_dataset()