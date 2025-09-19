# src/labeling/postprocess_labels.py
# Fill gaps between labels so applies_from = previous applies_to (continuous coverage).
# Overwrites labels.csv directly, no backups.

import os, csv, argparse
import pandas as pd

LABELS_CSV = "data/labels/labels.csv"

def fill_label_gaps(path: str = LABELS_CSV):
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found")

    df = pd.read_csv(path)
    if df.empty:
        print("[labels] File is empty, nothing to do.")
        return

    # Ensure sorted by start time
    df = df.sort_values("applies_from").reset_index(drop=True)

    # Force applies_from to match previous applies_to
    for i in range(1, len(df)):
        df.loc[i, "applies_from"] = df.loc[i - 1, "applies_to"]

    # Overwrite the file in place
    df.to_csv(path, index=False)
    print(f"[labels] Gaps filled and file updated in place → {path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default=LABELS_CSV,
                        help="Path to labels.csv (default: data/labels/labels.csv)")
    args = parser.parse_args()

    fill_label_gaps(args.file)

if __name__ == "__main__":
    main()