# src/features/windowing.py
# Read NDJSON logs and slice events into fixed windows.

import json, os, glob
import pandas as pd
from typing import Optional

def read_ndjson(path: str) -> pd.DataFrame:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            rows.append(json.loads(s))
    if not rows:
        return pd.DataFrame(columns=["t","type","x","y","dx","dy","btn","is_backspace","special"])

    df = pd.DataFrame(rows)
    # Ensure expected columns exist
    for c in ["x","y","dx","dy","btn","is_backspace","special"]:
        if c not in df.columns:
            df[c] = pd.NA

    df = df.sort_values("t").reset_index(drop=True)
    return df

def add_window_index(df: pd.DataFrame, window_ms: int = 60_000, base_ts_ms: Optional[int] = None) -> pd.DataFrame:
    """Assign an integer window_id per event. If base_ts_ms not given, min(t) is used."""
    if df.empty:
        df["window_id"] = []
        return df
    t0 = int(df["t"].min()) if base_ts_ms is None else int(base_ts_ms)
    df["window_id"] = (df["t"] - t0) // window_ms
    return df

def latest_raw_file(raw_dir: str = "data/raw") -> str:
    files = sorted(glob.glob(os.path.join(raw_dir, "events_*.ndjson")))
    if not files:
        raise FileNotFoundError(f"No NDJSON files found in {raw_dir}")
    return files[-1]