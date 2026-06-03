"""
train_model.py
Trains Isolation Forest anomaly detection model on Promobile KPI data.
Saves model, scaler, evaluation report, and anomaly results CSV.
"""

import pandas as pd
import numpy as np
import os, json, joblib, warnings
from datetime import datetime

from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, confusion_matrix,
    precision_score, recall_score, f1_score, roc_auc_score
)

warnings.filterwarnings("ignore")

BASE_DIR   = os.path.join(os.path.dirname(__file__), "..")
RAW_PATH   = os.path.join(BASE_DIR, "data", "raw",       "kpi_data.parquet")
PROC_DIR   = os.path.join(BASE_DIR, "data", "processed")
MODEL_DIR  = os.path.join(BASE_DIR, "models")

os.makedirs(PROC_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

KPI_COLS = [
    "latency_ms", "packet_loss_pct", "signal_strength_dbm",
    "call_drop_rate", "throughput_mbps", "active_users",
    "interference_ratio", "availability_pct"
]


def load_and_prepare(sample_per_tower: int = 8000):
    """Load data, build features, return X, y."""
    print("Loading raw data...")
    df = pd.read_parquet(RAW_PATH)
    print(f"Full dataset: {len(df):,} rows")

    # stratified sample per tower for training speed
    print(f"Sampling {sample_per_tower:,} rows per tower...")
    chunks = []
    for tid, grp in df.groupby("tower_id"):
        grp = grp.sort_values("timestamp").reset_index(drop=True)
        # rolling features per tower
        for col in KPI_COLS:
            grp[f"{col}_roll_mean"] = grp[col].rolling(48, min_periods=1).mean()
            grp[f"{col}_roll_std"]  = grp[col].rolling(48, min_periods=1).std().fillna(0)
            grp[f"{col}_zscore"]    = (
                (grp[col] - grp[f"{col}_roll_mean"]) /
                grp[f"{col}_roll_std"].replace(0, np.nan)
            ).fillna(0)
            grp[f"{col}_delta"]     = grp[col].diff().fillna(0)

        ts = pd.to_datetime(grp["timestamp"])
        grp["hour"]         = ts.dt.hour
        grp["day_of_week"]  = ts.dt.dayofweek
        grp["is_peak_hour"] = ts.dt.hour.between(8, 22).astype(int)
        grp["hour_sin"]     = np.sin(2 * np.pi * ts.dt.hour / 24)
        grp["hour_cos"]     = np.cos(2 * np.pi * ts.dt.hour / 24)

        # composite health score
        grp["network_health_score"] = (
            0.25 * (1 - (grp["latency_ms"].clip(5,300)-5)/295).clip(0,1) +
            0.20 * (1 - grp["packet_loss_pct"].clip(0,100)/100).clip(0,1) +
            0.15 * ((grp["signal_strength_dbm"].clip(-120,-40)+120)/80).clip(0,1) +
            0.20 * (1 - grp["call_drop_rate"].clip(0,1)).clip(0,1) +
            0.15 * (grp["throughput_mbps"].clip(1,500)/500).clip(0,1) +
            0.05 * (grp["availability_pct"].clip(90,100)-90)/10
        ) * 100

        n = min(sample_per_tower, len(grp))
        # keep all anomalies + random normal rows
        anom = grp[grp["is_anomaly"] == 1]
        norm = grp[grp["is_anomaly"] == 0].sample(
            min(n - len(anom), len(grp[grp["is_anomaly"]==0])),
            random_state=42
        )
        chunks.append(pd.concat([anom, norm]))

    data = pd.concat(chunks, ignore_index=True)
    print(f"Training sample: {len(data):,} rows | anomalies: {data['is_anomaly'].sum():,}")

    exclude = {"timestamp","tower_id","is_anomaly","anomaly_type","severity"}
    feat_cols = [c for c in data.columns if c not in exclude]

    X = data[feat_cols].fillna(0).astype(float)
    y = data["is_anomaly"].values
    meta = data[["timestamp","tower_id","anomaly_type","severity"]].reset_index(drop=True)
    return X, y, meta, feat_cols


def train_isolation_forest(X_train, contamination=0.015):
    print("\nTraining Isolation Forest...")
    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        max_samples=0.8,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train)
    return model


def train_random_forest_classifier(X_train, y_train):
    print("Training Random Forest classifier (supervised)...")
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    clf.fit(X_train, y_train)
    return clf


def evaluate(y_true, y_pred_if, y_pred_rf, y_proba_rf, feat_cols, clf):
    print("\n" + "="*50)
    print("MODEL EVALUATION REPORT")
    print("="*50)

    # Isolation Forest: convert {-1, 1} → {1, 0}
    y_if = np.where(y_pred_if == -1, 1, 0)

    metrics = {}
    for name, pred in [("Isolation Forest", y_if), ("Random Forest", y_pred_rf)]:
        p  = precision_score(y_true, pred, zero_division=0)
        r  = recall_score(y_true, pred, zero_division=0)
        f1 = f1_score(y_true, pred, zero_division=0)
        print(f"\n{name}:")
        print(f"  Precision : {p:.4f}")
        print(f"  Recall    : {r:.4f}")
        print(f"  F1 Score  : {f1:.4f}")
        print(classification_report(y_true, pred, target_names=["Normal","Anomaly"]))
        metrics[name] = {"precision": round(p,4), "recall": round(r,4), "f1": round(f1,4)}

    auc = roc_auc_score(y_true, y_proba_rf[:,1])
    print(f"Random Forest ROC-AUC: {auc:.4f}")
    metrics["Random Forest"]["roc_auc"] = round(auc, 4)

    # Feature importance
    importances = pd.Series(clf.feature_importances_, index=feat_cols)\
                    .sort_values(ascending=False).head(15)
    print("\nTop 15 Feature Importances (Random Forest):")
    for feat, imp in importances.items():
        print(f"  {feat:<40} {imp:.4f}")

    metrics["feature_importances"] = importances.round(4).to_dict()
    metrics["evaluated_at"] = str(datetime.now())
    return metrics, importances


def main():
    print("="*60)
    print("Promobile Anomaly Detection — Model Training")
    print("="*60)

    X, y, meta, feat_cols = load_and_prepare(sample_per_tower=8000)

    # scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # train/test split
    X_tr, X_te, y_tr, y_te, meta_tr, meta_te = train_test_split(
        X_scaled, y, meta, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\nTrain: {X_tr.shape} | Test: {X_te.shape}")
    print(f"Test anomaly rate: {y_te.mean()*100:.2f}%")

    # train models
    iso = train_isolation_forest(X_tr)
    clf = train_random_forest_classifier(X_tr, y_tr)

    # predictions
    y_pred_if = iso.predict(X_te)
    y_pred_rf = clf.predict(X_te)
    y_prob_rf  = clf.predict_proba(X_te)

    # evaluate
    metrics, feat_imp = evaluate(y_te, y_pred_if, y_pred_rf, y_prob_rf, feat_cols, clf)

    # save anomaly results
    te_df = pd.DataFrame(X_te, columns=feat_cols)
    te_df["is_anomaly_true"]   = y_te
    te_df["if_prediction"]     = np.where(y_pred_if == -1, 1, 0)
    te_df["rf_prediction"]     = y_pred_rf
    te_df["rf_anomaly_prob"]   = y_prob_rf[:, 1].round(4)
    te_df["if_score"]          = iso.score_samples(X_te).round(4)
    te_df = pd.concat([meta_te.reset_index(drop=True), te_df], axis=1)

    results_path = os.path.join(PROC_DIR, "anomaly_results.parquet")
    te_df.to_parquet(results_path, index=False)
    print(f"\nAnomaly results saved → {results_path}")

    # save feature importance CSV
    fi_df = feat_imp.reset_index()
    fi_df.columns = ["feature", "importance"]
    fi_df.to_csv(os.path.join(MODEL_DIR, "feature_importance.csv"), index=False)

    # save models & scaler
    joblib.dump(iso,    os.path.join(MODEL_DIR, "isolation_forest.pkl"))
    joblib.dump(clf,    os.path.join(MODEL_DIR, "random_forest.pkl"))
    joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.pkl"))
    joblib.dump(feat_cols, os.path.join(MODEL_DIR, "feature_columns.pkl"))
    print("Models saved → models/")

    # save evaluation report
    with open(os.path.join(MODEL_DIR, "evaluation_report.json"), "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    print("Evaluation report saved → models/evaluation_report.json")

    print("\n" + "="*60)
    print("Training complete!")
    print(f"  Random Forest F1  : {metrics['Random Forest']['f1']}")
    print(f"  ROC-AUC           : {metrics['Random Forest']['roc_auc']}")
    print("="*60)

if __name__ == "__main__":
    main()
