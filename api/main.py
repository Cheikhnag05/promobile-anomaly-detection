"""
api/main.py — Promobile Anomaly Detection REST API
FastAPI app exposing model predictions as endpoints.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import pandas as pd
import numpy as np
import joblib
import os
import json
from datetime import datetime

BASE_DIR  = os.path.join(os.path.dirname(__file__), "..")
MODEL_DIR = os.path.join(BASE_DIR, "models")
DATA_DIR  = os.path.join(BASE_DIR, "data", "processed")

app = FastAPI(
    title="Promobile Network Anomaly Detection API",
    description=(
        "Real-time telecom KPI anomaly detection powered by Isolation Forest "
        "& Random Forest. Built on 8M rows of Senegalese network data. "
        "Inspired by Promobile operations, Dakar 2025."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load models once at startup ──────────────────────────────────────────────
_iso       = None
_clf       = None
_scaler    = None
_feat_cols = None
_results   = None


def load_models():
    global _iso, _clf, _scaler, _feat_cols, _results
    try:
        _iso       = joblib.load(os.path.join(MODEL_DIR, "isolation_forest.pkl"))
        _clf       = joblib.load(os.path.join(MODEL_DIR, "random_forest.pkl"))
        _scaler    = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
        _feat_cols = joblib.load(os.path.join(MODEL_DIR, "feature_columns.pkl"))
        rp = os.path.join(DATA_DIR, "anomaly_results.parquet")
        if os.path.exists(rp):
            _results = pd.read_parquet(rp)
    except Exception as e:
        print(f"Warning: could not load models — {e}")


load_models()


# ── Schemas ──────────────────────────────────────────────────────────────────
class KPIInput(BaseModel):
    tower_id:              str   = Field("TW-001", example="TW-001")
    latency_ms:            float = Field(25.0,  ge=0,   le=5000)
    packet_loss_pct:       float = Field(0.5,   ge=0,   le=100)
    signal_strength_dbm:   float = Field(-70.0, ge=-130, le=-20)
    call_drop_rate:        float = Field(0.02,  ge=0,   le=1)
    throughput_mbps:       float = Field(80.0,  ge=0,   le=1000)
    active_users:          int   = Field(200,   ge=0,   le=10000)
    interference_ratio:    float = Field(0.1,   ge=0,   le=1)
    availability_pct:      float = Field(99.5,  ge=0,   le=100)
    hour:                  int   = Field(12,    ge=0,   le=23)
    is_peak:               int   = Field(1,     ge=0,   le=1)


class PredictionResponse(BaseModel):
    tower_id:           str
    is_anomaly:         bool
    anomaly_probability: float
    severity:           str
    isolation_forest_score: float
    dominant_kpi:       str
    recommendation:     str
    predicted_at:       str


class HealthResponse(BaseModel):
    status:    str
    models_loaded: bool
    version:   str
    total_results: int


# ── Helper ───────────────────────────────────────────────────────────────────
def build_feature_vector(inp: KPIInput) -> np.ndarray:
    """Build a feature vector matching training feature columns."""
    base = {
        "latency_ms":           inp.latency_ms,
        "packet_loss_pct":      inp.packet_loss_pct,
        "signal_strength_dbm":  inp.signal_strength_dbm,
        "call_drop_rate":       inp.call_drop_rate,
        "throughput_mbps":      inp.throughput_mbps,
        "active_users":         inp.active_users,
        "interference_ratio":   inp.interference_ratio,
        "availability_pct":     inp.availability_pct,
        "hour":                 inp.hour,
        "is_peak":              inp.is_peak,
        "hour_sin":             np.sin(2 * np.pi * inp.hour / 24),
        "hour_cos":             np.cos(2 * np.pi * inp.hour / 24),
        "health":               (
            0.25 * (1 - (inp.latency_ms - 5) / 295) +
            0.20 * (1 - inp.packet_loss_pct / 100) +
            0.20 * (1 - inp.call_drop_rate) +
            0.15 * (inp.throughput_mbps / 500)
        ) * 100,
    }
    kpi_cols = ["latency_ms","packet_loss_pct","signal_strength_dbm",
                "call_drop_rate","throughput_mbps","active_users",
                "interference_ratio","availability_pct"]
    for col in kpi_cols:
        base[f"{col}_rmean"]  = base[col]
        base[f"{col}_rstd"]   = 0.0
        base[f"{col}_zscore"] = 0.0
        base[f"{col}_delta"]  = 0.0

    if _feat_cols:
        vec = np.array([base.get(f, 0.0) for f in _feat_cols], dtype=float)
    else:
        vec = np.array(list(base.values()), dtype=float)
    return vec.reshape(1, -1)


def severity_from_prob(prob: float) -> str:
    if prob < 0.3:   return "low"
    if prob < 0.6:   return "medium"
    if prob < 0.85:  return "high"
    return "critical"


def dominant_kpi(inp: KPIInput) -> str:
    scores = {
        "latency_ms":          inp.latency_ms / 300,
        "packet_loss_pct":     inp.packet_loss_pct / 100,
        "call_drop_rate":      inp.call_drop_rate,
        "interference_ratio":  inp.interference_ratio,
        "low_throughput":      1 - inp.throughput_mbps / 500,
        "low_signal":          (inp.signal_strength_dbm + 120) / 80 * -1 + 1,
    }
    return max(scores, key=scores.get)


RECOMMENDATIONS = {
    "latency_ms":        "Investigate backhaul congestion. Check routing tables for TW.",
    "packet_loss_pct":   "Run packet trace. Likely fiber degradation or switch fault.",
    "call_drop_rate":    "Check handover parameters. Review neighboring cell overlap.",
    "interference_ratio":"Frequency audit required. Possible co-channel interference.",
    "low_throughput":    "Capacity threshold reached. Consider sector expansion.",
    "low_signal":        "RF survey needed. Check antenna alignment and tilt.",
}


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/", tags=["General"])
def root():
    return {
        "message": "Promobile Anomaly Detection API",
        "docs":    "/docs",
        "health":  "/health",
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
def health():
    return HealthResponse(
        status="ok",
        models_loaded=_clf is not None,
        version="1.0.0",
        total_results=len(_results) if _results is not None else 0,
    )


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
def predict(inp: KPIInput):
    if _clf is None or _scaler is None:
        raise HTTPException(503, detail="Models not loaded. Run train_model.py first.")
    try:
        X = build_feature_vector(inp)
        Xs = _scaler.transform(X)
        rf_prob   = float(_clf.predict_proba(Xs)[0][1])
        is_anom   = bool(rf_prob >= 0.5)
        if_score  = float(_iso.score_samples(Xs)[0])
        sev       = severity_from_prob(rf_prob) if is_anom else "none"
        dom       = dominant_kpi(inp)
        rec       = RECOMMENDATIONS.get(dom, "Monitor KPIs. No immediate action required.")
        if not is_anom:
            rec = "All KPIs within normal range. No action required."
        return PredictionResponse(
            tower_id=inp.tower_id,
            is_anomaly=is_anom,
            anomaly_probability=round(rf_prob, 4),
            severity=sev,
            isolation_forest_score=round(if_score, 4),
            dominant_kpi=dom,
            recommendation=rec,
            predicted_at=str(datetime.now()),
        )
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/anomalies", tags=["Data"])
def get_anomalies(
    tower_id:  Optional[str] = Query(None),
    severity:  Optional[str] = Query(None),
    limit:     int           = Query(100, ge=1, le=1000),
    offset:    int           = Query(0,   ge=0),
):
    if _results is None:
        raise HTTPException(503, detail="Results not loaded.")
    df = _results[_results["is_anomaly_true"] == 1].copy()
    if tower_id:
        df = df[df["tower_id"] == tower_id]
    if severity:
        df = df[df["severity"] == severity]
    total = len(df)
    page  = df.iloc[offset: offset + limit]
    return {
        "total":   total,
        "offset":  offset,
        "limit":   limit,
        "results": page[["timestamp","tower_id","anomaly_type","severity","rf_prob"]].to_dict("records"),
    }


@app.get("/stats", tags=["Data"])
def get_stats():
    if _results is None:
        raise HTTPException(503, detail="Results not loaded.")
    rpt_path = os.path.join(MODEL_DIR, "evaluation_report.json")
    report   = {}
    if os.path.exists(rpt_path):
        with open(rpt_path) as f:
            report = json.load(f)
    df  = _results
    adf = df[df["is_anomaly_true"] == 1]
    return {
        "total_records":    len(df),
        "total_anomalies":  int(adf.shape[0]),
        "anomaly_rate_pct": round(adf.shape[0] / len(df) * 100, 2),
        "by_severity":      adf["severity"].value_counts().to_dict() if "severity" in adf.columns else {},
        "by_type":          adf["anomaly_type"].value_counts().to_dict() if "anomaly_type" in adf.columns else {},
        "model_performance": report,
    }
