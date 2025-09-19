# src/features/postprocess.py
# Lightweight cleanup for demo: fill NAs, clip ratios, optional z-score normalization.

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List, Optional

NUMERIC_FEATURES: List[str] = [
    "keys_total","backspace","correction_rate",
    "avg_iki","iki_std",
    "move_events","mouse_speed_mean","mouse_speed_std","mouse_jerk_mean",
    "idle_ratio","clicks","scrolls","tod_sin","tod_cos"
]

def fill_and_clip(feats: pd.DataFrame) -> pd.DataFrame:
    out = feats.copy()
    # Fill NaNs: timing stats to 0 for demo, speeds/jerk to 0, keep ratios bounded.
    out["avg_iki"] = out["avg_iki"].fillna(0.0)
    out["iki_std"] = out["iki_std"].fillna(0.0)
    for c in ["mouse_speed_mean","mouse_speed_std","mouse_jerk_mean"]:
        out[c] = out[c].fillna(0.0)
    out["correction_rate"] = out["correction_rate"].fillna(0.0)
    out["idle_ratio"] = out["idle_ratio"].clip(lower=0.0, upper=1.0).fillna(0.0)
    # Any other numeric NA → 0
    for c in NUMERIC_FEATURES:
        if c in out.columns:
            out[c] = out[c].fillna(0.0)
    return out

def zscore_fit(feats: pd.DataFrame) -> Dict[str, Tuple[float,float]]:
    stats: Dict[str, Tuple[float,float]] = {}
    for c in NUMERIC_FEATURES:
        if c in feats.columns:
            mu = float(np.mean(feats[c]))
            sd = float(np.std(feats[c], ddof=0))
            stats[c] = (mu, sd if sd > 1e-8 else 1.0)
    return stats

def zscore_apply(feats: pd.DataFrame, stats: Dict[str, Tuple[float,float]]) -> pd.DataFrame:
    out = feats.copy()
    for c, (mu, sd) in stats.items():
        if c in out.columns:
            out[c] = (out[c] - mu) / sd
    return out