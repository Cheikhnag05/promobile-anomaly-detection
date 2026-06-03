"""
features.py
Feature engineering for telecom KPI anomaly detection.
Builds rolling stats, z-scores, lag features, and time features.
"""

import pandas as pd
import numpy as np
import os

KPI_COLS = [
    "latency_ms", "packet_loss_pct", "signal_strength_dbm",
    "call_drop_rate", "throughput_mbps", "active_users",
    "interference_ratio", "availability_pct"
]

WINDOWS = [12, 48, 168]   # ~1h, ~4h, ~1 week (at 5-min intervals)


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    ts = pd.to_datetime(df["timestamp"])
    df["hour"]          = ts.dt.hour
    df["day_of_week"]   = ts.dt.dayofweek
    df["month"]         = ts.dt.month
    df["is_weekend"]    = (ts.dt.dayofweek >= 5).astype(int)
    df["is_peak_hour"]  = ts.dt.hour.between(8, 22).astype(int)
    df["hour_sin"]      = np.sin(2 * np.pi * ts.dt.hour / 24)
    df["hour_cos"]      = np.cos(2 * np.pi * ts.dt.hour / 24)
    df["dow_sin"]       = np.sin(2 * np.pi * ts.dt.dayofweek / 7)
    df["dow_cos"]       = np.cos(2 * np.pi * ts.dt.dayofweek / 7)
    return df


def add_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().sort_values("timestamp")
    for col in KPI_COLS:
        for w in WINDOWS:
            roll = df[col].rolling(window=w, min_periods=1)
            df[f"{col}_roll_mean_{w}"] = roll.mean().round(4)
            df[f"{col}_roll_std_{w}"]  = roll.std().fillna(0).round(4)
    return df


def add_zscore_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in KPI_COLS:
        w = WINDOWS[1]  # 48-window z-score
        mean_col = f"{col}_roll_mean_{w}"
        std_col  = f"{col}_roll_std_{w}"
        if mean_col in df.columns and std_col in df.columns:
            std = df[std_col].replace(0, np.nan)
            df[f"{col}_zscore"] = ((df[col] - df[mean_col]) / std).fillna(0).round(3)
    return df


def add_lag_features(df: pd.DataFrame, lags=(1, 3, 6)) -> pd.DataFrame:
    df = df.copy()
    for col in ["latency_ms", "packet_loss_pct", "call_drop_rate", "throughput_mbps"]:
        for lag in lags:
            df[f"{col}_lag_{lag}"] = df[col].shift(lag).fillna(method="bfill")
    return df


def add_delta_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in KPI_COLS:
        df[f"{col}_delta"] = df[col].diff().fillna(0).round(4)
    return df


def add_composite_score(df: pd.DataFrame) -> pd.DataFrame:
    """Composite network health score 0–100 (higher = healthier)."""
    df = df.copy()
    lat_norm  = (1 - (df["latency_ms"].clip(5, 300) - 5) / 295).clip(0, 1)
    pkt_norm  = (1 - df["packet_loss_pct"].clip(0, 100) / 100).clip(0, 1)
    sig_norm  = ((df["signal_strength_dbm"].clip(-120, -40) + 120) / 80).clip(0, 1)
    cdr_norm  = (1 - df["call_drop_rate"].clip(0, 1)).clip(0, 1)
    thr_norm  = (df["throughput_mbps"].clip(1, 500) / 500).clip(0, 1)
    avail_norm = (df["availability_pct"].clip(90, 100) - 90) / 10

    df["network_health_score"] = (
        0.25 * lat_norm +
        0.20 * pkt_norm +
        0.15 * sig_norm +
        0.20 * cdr_norm +
        0.15 * thr_norm +
        0.05 * avail_norm
    ).round(4) * 100
    return df


def build_features(df: pd.DataFrame, per_tower: bool = True) -> pd.DataFrame:
    """Full feature pipeline."""
    df = add_time_features(df)
    df = add_delta_features(df)
    df = add_composite_score(df)

    if per_tower:
        chunks = []
        for tid, grp in df.groupby("tower_id"):
            grp = grp.sort_values("timestamp").reset_index(drop=True)
            grp = add_rolling_features(grp)
            grp = add_zscore_features(grp)
            grp = add_lag_features(grp)
            chunks.append(grp)
        df = pd.concat(chunks, ignore_index=True)
    else:
        df = add_rolling_features(df)
        df = add_zscore_features(df)
        df = add_lag_features(df)

    return df


def get_feature_columns(df: pd.DataFrame) -> list:
    exclude = {"timestamp", "tower_id", "is_anomaly", "anomaly_type", "severity"}
    return [c for c in df.columns if c not in exclude]


if __name__ == "__main__":
    raw_path  = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "kpi_data.parquet")
    proc_path = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
    os.makedirs(proc_path, exist_ok=True)

    print("Loading raw data...")
    df = pd.read_parquet(raw_path)
    print(f"Raw shape: {df.shape}")

    print("Building features (per-tower rolling stats)...")
    # use sample for speed during dev; full run in train_model
    sample = df.groupby("tower_id").apply(lambda x: x.head(5000)).reset_index(drop=True)
    featured = build_features(sample, per_tower=True)
    out = os.path.join(proc_path, "features_sample.parquet")
    featured.to_parquet(out, index=False)
    print(f"Features saved → {out}")
    print(f"Feature count  : {len(get_feature_columns(featured))}")
    print(f"Sample shape   : {featured.shape}")
