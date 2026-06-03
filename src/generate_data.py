"""
generate_data.py
Simulates 8M rows of daily telecom KPI data for 50 cell towers
across Senegal. Injects realistic anomalies at known timestamps.
Inspired by Promobile network operations data (Dakar, 2025).
"""

import numpy as np
import pandas as pd
from datetime import datetime
import os
import json

SEED = 42
np.random.seed(SEED)

N_TOWERS = 50
ROWS_PER_TOWER = 160_000
START_DATE = datetime(2024, 1, 1)
END_DATE   = datetime(2024, 12, 31)

SENEGAL_DISTRICTS = [
    "Plateau","Médina","Gueule Tapée","Fann","Point E",
    "Mermoz","Sacré-Cœur","Ouakam","Ngor","Almadies",
    "Parcelles Assainies","Pikine","Guédiawaye","Rufisque","Bargny",
    "Thiès","Mbour","Kaolack","Ziguinchor","Saint-Louis",
    "Touba","Diourbel","Fatick","Tambacounda","Kolda",
    "Vélingara","Sédhiou","Kédougou","Matam","Podor",
    "Louga","Linguère","Kebemer","Tivaouane","Joal",
    "Saly","Kafrine","Birkelane","Kaffrine","Malème Hodar",
    "Bignona","Oussouye","Ziguinchor Sud","Kolda Nord","Kolda Sud",
    "Bakel","Kidira","Goudiry","Saraya","Kéniéba"
]

TOWER_TYPES = ["macro","micro","small_cell","rooftop"]

ANOMALY_TYPES = [
    "latency_spike","packet_loss_burst","signal_degradation",
    "call_drop_surge","throughput_collapse","interference_event"
]


def generate_tower_metadata(n=N_TOWERS):
    rng = np.random.default_rng(SEED)
    towers = []
    for i in range(n):
        lat = 14.6928 + rng.uniform(-3.0, 1.5)
        lon = -17.4467 + rng.uniform(-3.0, 3.0)
        towers.append({
            "tower_id":       f"TW-{i+1:03d}",
            "district":       SENEGAL_DISTRICTS[i % len(SENEGAL_DISTRICTS)],
            "tower_type":     rng.choice(TOWER_TYPES, p=[0.5,0.25,0.15,0.10]),
            "latitude":       round(float(lat), 5),
            "longitude":      round(float(lon), 5),
            "capacity_users": int(rng.integers(500, 5000)),
            "install_year":   int(rng.integers(2015, 2023)),
        })
    return pd.DataFrame(towers)


def inject_anomalies(df, anomaly_fraction=0.015):
    rng = np.random.default_rng(SEED + hash(df["tower_id"].iloc[0]) % 10000)
    n = len(df)
    n_anomalies = int(n * anomaly_fraction)

    burst_starts = rng.choice(max(1, n - 50), size=max(1, n_anomalies // 20), replace=False)
    burst_idx = []
    for s in burst_starts:
        length = int(rng.integers(5, 50))
        burst_idx.extend(range(s, min(s + length, n)))

    base_idx = rng.choice(n, size=n_anomalies // 2, replace=False)
    anomaly_indices = np.unique(np.concatenate([base_idx, burst_idx]))[:n_anomalies]

    labels    = np.zeros(n, dtype=int)
    atypes    = np.full(n, "normal", dtype=object)
    severities = np.full(n, "none", dtype=object)

    for idx in anomaly_indices:
        atype = rng.choice(ANOMALY_TYPES)
        sev   = rng.choice(["low","medium","high","critical"], p=[0.4,0.3,0.2,0.1])
        mul   = {"low":2.0,"medium":3.5,"high":6.0,"critical":10.0}[sev]
        labels[idx]     = 1
        atypes[idx]     = atype
        severities[idx] = sev

        if atype == "latency_spike":
            df.at[df.index[idx], "latency_ms"] = min(df["latency_ms"].iloc[idx] * mul, 2000)
        elif atype == "packet_loss_burst":
            df.at[df.index[idx], "packet_loss_pct"] = min(df["packet_loss_pct"].iloc[idx] * mul, 100.0)
        elif atype == "signal_degradation":
            df.at[df.index[idx], "signal_strength_dbm"] = max(df["signal_strength_dbm"].iloc[idx] - mul * 8, -120)
        elif atype == "call_drop_surge":
            df.at[df.index[idx], "call_drop_rate"] = min(df["call_drop_rate"].iloc[idx] * mul, 1.0)
        elif atype == "throughput_collapse":
            df.at[df.index[idx], "throughput_mbps"] = max(df["throughput_mbps"].iloc[idx] / mul, 0.1)
        elif atype == "interference_event":
            df.at[df.index[idx], "interference_ratio"] = min(df["interference_ratio"].iloc[idx] * mul, 1.0)

    df["is_anomaly"]   = labels
    df["anomaly_type"] = atypes
    df["severity"]     = severities
    return df


def generate_tower_kpis(tower_id, tower_type, n_rows=ROWS_PER_TOWER):
    rng = np.random.default_rng(SEED + hash(tower_id) % 10000)
    timestamps = pd.date_range(START_DATE, END_DATE, periods=n_rows)
    hours      = timestamps.hour.values
    hour_factor = (1.0 + 0.6 * np.sin((hours - 6) * np.pi / 12)).clip(0)
    dow_factor  = np.where(timestamps.dayofweek < 5, 1.1, 0.85)

    adj = {"macro":1.0,"micro":0.85,"small_cell":0.7,"rooftop":0.9}.get(tower_type, 1.0)
    n   = n_rows

    latency     = np.abs(20*adj + 15*hour_factor*dow_factor + rng.normal(0,5,n)).clip(5,300).round(2)
    pkt_loss    = np.abs(0.5*adj + 0.8*hour_factor + rng.normal(0,0.3,n)).clip(0,100).round(3)
    signal      = (-65 - 10*adj + rng.normal(0,4,n)).clip(-120,-40).round(1)
    call_drop   = np.abs(0.02*adj + 0.015*hour_factor + rng.normal(0,0.008,n)).clip(0,1).round(4)
    throughput  = np.abs(80/adj + 40*hour_factor*dow_factor + rng.normal(0,10,n)).clip(1,500).round(2)
    users       = np.abs(200*adj*hour_factor*dow_factor + rng.normal(0,30,n)).astype(int).clip(0,5000)
    interference= np.abs(0.1*adj + 0.05*hour_factor + rng.normal(0,0.03,n)).clip(0,1).round(4)
    availability= np.abs(99.5 + rng.normal(0,0.2,n)).clip(90,100).round(3)

    df = pd.DataFrame({
        "timestamp":            timestamps,
        "tower_id":             tower_id,
        "latency_ms":           latency,
        "packet_loss_pct":      pkt_loss,
        "signal_strength_dbm":  signal,
        "call_drop_rate":       call_drop,
        "throughput_mbps":      throughput,
        "active_users":         users,
        "interference_ratio":   interference,
        "availability_pct":     availability,
    })
    return inject_anomalies(df)


def main():
    print("="*60)
    print("Promobile KPI Data Generator")
    print(f"Generating {N_TOWERS*ROWS_PER_TOWER:,} rows across {N_TOWERS} towers...")
    print("="*60)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
    os.makedirs(out_dir, exist_ok=True)

    towers = generate_tower_metadata()
    towers.to_csv(os.path.join(out_dir, "tower_metadata.csv"), index=False)
    print(f"Tower metadata saved ({len(towers)} towers)")

    chunks, total_anomalies = [], 0
    for i, row in towers.iterrows():
        df = generate_tower_kpis(row["tower_id"], row["tower_type"])
        chunks.append(df)
        n_anom = int(df["is_anomaly"].sum())
        total_anomalies += n_anom
        if (i+1) % 10 == 0:
            print(f"  [{i+1:02d}/50] {row['tower_id']} ({row['district']}) — "
                  f"{len(df):,} rows, {n_anom:,} anomalies")

    print("\nConcatenating all towers...")
    full = pd.concat(chunks, ignore_index=True).sort_values("timestamp").reset_index(drop=True)

    out_path = os.path.join(out_dir, "kpi_data.parquet")
    full.to_parquet(out_path, index=False, compression="snappy")

    print(f"\nDataset saved  → {out_path}")
    print(f"Total rows     : {len(full):,}")
    print(f"Total anomalies: {total_anomalies:,} ({total_anomalies/len(full)*100:.2f}%)")

    stats = {
        "total_rows": len(full),
        "total_anomalies": total_anomalies,
        "anomaly_rate_pct": round(total_anomalies/len(full)*100, 2),
        "towers": N_TOWERS,
        "date_start": str(full["timestamp"].min()),
        "date_end":   str(full["timestamp"].max()),
        "anomaly_types": full[full["is_anomaly"]==1]["anomaly_type"].value_counts().to_dict(),
        "severity_dist": full[full["is_anomaly"]==1]["severity"].value_counts().to_dict(),
    }
    with open(os.path.join(out_dir, "dataset_stats.json"), "w") as f:
        json.dump(stats, f, indent=2, default=str)

    print("Stats saved    → data/raw/dataset_stats.json")
    print("="*60)
    return full, towers

if __name__ == "__main__":
    main()
