# src/features/compute_core.py
# Minimal feature set for demo (keyboard, mouse, time-of-day). Contentless-safe.

import numpy as np
import pandas as pd
from math import pi, sin, cos
from typing import Tuple, List

FEATURE_COLUMNS: List[str] = [
    "window_id","t_start","t_end",
    "keys_total","backspace","correction_rate",
    "avg_iki","iki_std",
    "move_events","mouse_speed_mean","mouse_speed_std","mouse_jerk_mean",
    "idle_ratio","clicks","scrolls","tod_sin","tod_cos"
]

def _tod_features(ts_ms: int) -> Tuple[float, float]:
    seconds = (ts_ms // 1000) % 86400
    theta = 2 * pi * (seconds / 86400.0)
    return sin(theta), cos(theta)

def compute_window_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Expects df columns: t,type,x,y,dx,dy,is_backspace,special,window_id
    Returns one row per window_id with numeric features (columns in FEATURE_COLUMNS).
    """
    if df.empty:
        return pd.DataFrame(columns=FEATURE_COLUMNS)

    out = []
    for wid, chunk in df.groupby("window_id", sort=True):
        if chunk.empty:
            continue
        t_start = int(chunk["t"].min())
        t_end   = int(chunk["t"].max())
        # --- Keyboard features ---
        k = chunk[chunk["type"] == "key_down"].copy()
        keys_total = int(len(k))
        backspace = int(k["is_backspace"].fillna(False).astype(bool).sum())
        correction_rate = (backspace / keys_total) if keys_total > 0 else 0.0

        if keys_total >= 2:
            ikis = k["t"].astype("int64").diff().dropna().to_numpy(dtype=float)
            avg_iki = float(np.mean(ikis))
            iki_std = float(np.std(ikis, ddof=0))
        else:
            avg_iki, iki_std = float("nan"), float("nan")

        # --- Mouse dynamics ---
        mv = chunk[chunk["type"] == "mouse_move"].copy()
        move_events = int(len(mv))
        mouse_speed_mean = float("nan")
        mouse_speed_std  = float("nan")
        mouse_jerk_mean  = float("nan")

        if move_events >= 2:
            mv["dx"] = mv["x"].astype(float).diff()
            mv["dy"] = mv["y"].astype(float).diff()
            mv["dt"] = mv["t"].astype("int64").diff() / 1000.0  # seconds
            mv = mv.dropna()
            dist = np.sqrt(mv["dx"].to_numpy()**2 + mv["dy"].to_numpy()**2)
            dt = mv["dt"].replace(0, np.nan).to_numpy()
            speed = dist / dt
            mouse_speed_mean = float(np.nanmean(speed))
            mouse_speed_std  = float(np.nanstd(speed, ddof=0))
            accel = np.diff(speed) / dt[1:]  # aligned
            jerk = np.diff(accel)
            mouse_jerk_mean = float(np.nanmean(np.abs(jerk))) if jerk.size else float("nan")

        # Idle ratio via gaps in any events (>2s)
        gaps = chunk["t"].astype("int64").diff().fillna(0) / 1000.0
        idle_seconds = float(np.sum(gaps[gaps > 2.0]))
        idle_ratio = max(0.0, min(1.0, idle_seconds / 60.0))

        clicks  = int((chunk["type"] == "mouse_click").sum())
        scrolls = int((chunk["type"] == "mouse_scroll").sum())

        # Time-of-day from window midpoint
        mid_ts = (t_start + t_end) // 2
        tod_s, tod_c = _tod_features(mid_ts)

        out.append({
            "window_id": int(wid),
            "t_start": t_start, "t_end": t_end,
            "keys_total": keys_total,
            "backspace": backspace,
            "correction_rate": float(correction_rate),
            "avg_iki": float(avg_iki),
            "iki_std": float(iki_std),
            "move_events": move_events,
            "mouse_speed_mean": mouse_speed_mean,
            "mouse_speed_std": mouse_speed_std,
            "mouse_jerk_mean": mouse_jerk_mean,
            "idle_ratio": idle_ratio,
            "clicks": clicks, "scrolls": scrolls,
            "tod_sin": float(tod_s),
            "tod_cos": float(tod_c),
        })

    return pd.DataFrame(out, columns=FEATURE_COLUMNS)