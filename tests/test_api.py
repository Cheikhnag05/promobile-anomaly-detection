"""
tests/test_api.py
Full test suite for the Promobile Anomaly Detection API.
Covers: health, prediction, anomaly retrieval, stats, edge cases.
"""

import pytest
import numpy as np
import pandas as pd
import os, json, joblib
from fastapi.testclient import TestClient

# ensure we can import from api/
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api.main import app, load_models

client = TestClient(app)

# ── Fixtures ──────────────────────────────────────────────────────────────────
NORMAL_KPI = {
    "tower_id": "TW-001",
    "latency_ms": 22.5,
    "packet_loss_pct": 0.4,
    "signal_strength_dbm": -68.0,
    "call_drop_rate": 0.018,
    "throughput_mbps": 85.0,
    "active_users": 210,
    "interference_ratio": 0.09,
    "availability_pct": 99.6,
    "hour": 14,
    "is_peak": 1,
}

ANOMALOUS_KPI = {
    "tower_id": "TW-007",
    "latency_ms": 850.0,        # severe spike
    "packet_loss_pct": 45.0,    # very high
    "signal_strength_dbm": -115.0,
    "call_drop_rate": 0.92,
    "throughput_mbps": 2.0,
    "active_users": 3200,
    "interference_ratio": 0.95,
    "availability_pct": 91.0,
    "hour": 3,
    "is_peak": 0,
}


# ══════════════════════════════════════════════════════════════════════════════
# 1. HEALTH & ROOT
# ══════════════════════════════════════════════════════════════════════════════
class TestGeneral:
    def test_root_returns_200(self):
        r = client.get("/")
        assert r.status_code == 200

    def test_root_contains_docs_key(self):
        r = client.get("/")
        assert "docs" in r.json()

    def test_health_returns_200(self):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_schema(self):
        r = client.get("/health")
        data = r.json()
        assert "status" in data
        assert "models_loaded" in data
        assert "version" in data
        assert "total_results" in data

    def test_health_status_ok(self):
        r = client.get("/health")
        assert r.json()["status"] == "ok"

    def test_health_version_format(self):
        r = client.get("/health")
        version = r.json()["version"]
        parts = version.split(".")
        assert len(parts) == 3


# ══════════════════════════════════════════════════════════════════════════════
# 2. PREDICT ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════
class TestPredict:
    def test_predict_normal_returns_200(self):
        r = client.post("/predict", json=NORMAL_KPI)
        assert r.status_code == 200

    def test_predict_anomalous_returns_200(self):
        r = client.post("/predict", json=ANOMALOUS_KPI)
        assert r.status_code == 200

    def test_predict_response_schema(self):
        r = client.post("/predict", json=NORMAL_KPI)
        data = r.json()
        required = {
            "tower_id", "is_anomaly", "anomaly_probability",
            "severity", "isolation_forest_score", "dominant_kpi",
            "recommendation", "predicted_at"
        }
        assert required.issubset(set(data.keys()))

    def test_predict_tower_id_echoed(self):
        r = client.post("/predict", json=NORMAL_KPI)
        assert r.json()["tower_id"] == "TW-001"

    def test_predict_anomaly_prob_in_range(self):
        r = client.post("/predict", json=NORMAL_KPI)
        prob = r.json()["anomaly_probability"]
        assert 0.0 <= prob <= 1.0

    def test_predict_is_anomaly_is_bool(self):
        r = client.post("/predict", json=NORMAL_KPI)
        assert isinstance(r.json()["is_anomaly"], bool)

    def test_predict_normal_kpi_not_anomaly(self):
        r = client.post("/predict", json=NORMAL_KPI)
        # normal KPIs should yield low probability
        assert r.json()["anomaly_probability"] < 0.5

    def test_predict_anomalous_kpi_is_anomaly(self):
        r = client.post("/predict", json=ANOMALOUS_KPI)
        assert r.json()["is_anomaly"] is True

    def test_predict_anomalous_severity_not_none(self):
        r = client.post("/predict", json=ANOMALOUS_KPI)
        assert r.json()["severity"] != "none"

    def test_predict_normal_severity_none(self):
        r = client.post("/predict", json=NORMAL_KPI)
        assert r.json()["severity"] == "none"

    def test_predict_recommendation_not_empty(self):
        r = client.post("/predict", json=ANOMALOUS_KPI)
        assert len(r.json()["recommendation"]) > 0

    def test_predict_missing_field_uses_defaults(self):
        bad = {k: v for k, v in NORMAL_KPI.items() if k != "latency_ms"}
        r = client.post("/predict", json=bad)
        assert r.status_code == 200  # pydantic v2 uses field defaults

    def test_predict_latency_above_max_returns_422(self):
        bad = {**NORMAL_KPI, "latency_ms": 99999}
        r = client.post("/predict", json=bad)
        assert r.status_code == 422

    def test_predict_negative_packet_loss_returns_422(self):
        bad = {**NORMAL_KPI, "packet_loss_pct": -5.0}
        r = client.post("/predict", json=bad)
        assert r.status_code == 422

    def test_predict_call_drop_above_1_returns_422(self):
        bad = {**NORMAL_KPI, "call_drop_rate": 1.5}
        r = client.post("/predict", json=bad)
        assert r.status_code == 422

    def test_predict_hour_above_23_returns_422(self):
        bad = {**NORMAL_KPI, "hour": 25}
        r = client.post("/predict", json=bad)
        assert r.status_code == 422

    def test_predict_empty_body_uses_all_defaults(self):
        r = client.post("/predict", json={})
        assert r.status_code == 200  # all fields have defaults in pydantic v2

    def test_predict_isolation_forest_score_is_float(self):
        r = client.post("/predict", json=NORMAL_KPI)
        assert isinstance(r.json()["isolation_forest_score"], float)

    def test_predict_dominant_kpi_is_string(self):
        r = client.post("/predict", json=ANOMALOUS_KPI)
        assert isinstance(r.json()["dominant_kpi"], str)
        assert len(r.json()["dominant_kpi"]) > 0

    def test_predict_different_towers_independent(self):
        kpi2 = {**NORMAL_KPI, "tower_id": "TW-002"}
        r1 = client.post("/predict", json=NORMAL_KPI)
        r2 = client.post("/predict", json=kpi2)
        assert r1.json()["tower_id"] != r2.json()["tower_id"]

    def test_predict_boundary_latency(self):
        boundary = {**NORMAL_KPI, "latency_ms": 5.0}
        r = client.post("/predict", json=boundary)
        assert r.status_code == 200

    def test_predict_max_users(self):
        edge = {**NORMAL_KPI, "active_users": 10000}
        r = client.post("/predict", json=edge)
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# 3. ANOMALIES ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════
class TestAnomalies:
    def test_anomalies_returns_200(self):
        r = client.get("/anomalies")
        assert r.status_code == 200

    def test_anomalies_response_schema(self):
        r = client.get("/anomalies")
        data = r.json()
        assert "total" in data
        assert "results" in data
        assert "offset" in data
        assert "limit" in data

    def test_anomalies_default_limit_100(self):
        r = client.get("/anomalies")
        data = r.json()
        assert len(data["results"]) <= 100

    def test_anomalies_custom_limit(self):
        r = client.get("/anomalies?limit=10")
        assert len(r.json()["results"]) <= 10

    def test_anomalies_offset_pagination(self):
        r1 = client.get("/anomalies?limit=5&offset=0")
        r2 = client.get("/anomalies?limit=5&offset=5")
        ids1 = [x.get("tower_id") for x in r1.json()["results"]]
        ids2 = [x.get("tower_id") for x in r2.json()["results"]]
        # pages should differ (unless dataset tiny)
        if len(ids1) == 5 and len(ids2) == 5:
            assert ids1 != ids2

    def test_anomalies_severity_filter(self):
        r = client.get("/anomalies?severity=critical")
        for item in r.json()["results"]:
            assert item.get("severity") == "critical"

    def test_anomalies_tower_filter(self):
        r = client.get("/anomalies?tower_id=TW-001")
        for item in r.json()["results"]:
            assert item.get("tower_id") == "TW-001"

    def test_anomalies_total_is_int(self):
        r = client.get("/anomalies")
        assert isinstance(r.json()["total"], int)

    def test_anomalies_result_has_timestamp(self):
        r = client.get("/anomalies?limit=1")
        results = r.json()["results"]
        if results:
            assert "timestamp" in results[0]


# ══════════════════════════════════════════════════════════════════════════════
# 4. STATS ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════
class TestStats:
    def test_stats_returns_200(self):
        r = client.get("/stats")
        assert r.status_code == 200

    def test_stats_schema(self):
        r = client.get("/stats")
        data = r.json()
        assert "total_records" in data
        assert "total_anomalies" in data
        assert "anomaly_rate_pct" in data

    def test_stats_total_records_positive(self):
        r = client.get("/stats")
        assert r.json()["total_records"] > 0

    def test_stats_anomaly_rate_in_range(self):
        r = client.get("/stats")
        rate = r.json()["anomaly_rate_pct"]
        assert 0.0 <= rate <= 100.0

    def test_stats_model_performance_present(self):
        r = client.get("/stats")
        assert "model_performance" in r.json()


# ══════════════════════════════════════════════════════════════════════════════
# 5. DATA INTEGRITY
# ══════════════════════════════════════════════════════════════════════════════
class TestDataIntegrity:
    def test_dataset_exists(self):
        base = os.path.join(os.path.dirname(__file__), "..")
        path = os.path.join(base, "data", "raw", "kpi_data.parquet")
        assert os.path.exists(path)

    def test_dataset_row_count(self):
        base = os.path.join(os.path.dirname(__file__), "..")
        df = pd.read_parquet(os.path.join(base, "data", "raw", "kpi_data.parquet"))
        assert len(df) == 8_000_000

    def test_dataset_columns(self):
        base = os.path.join(os.path.dirname(__file__), "..")
        df = pd.read_parquet(os.path.join(base, "data", "raw", "kpi_data.parquet"))
        required = ["tower_id","timestamp","latency_ms","packet_loss_pct",
                    "is_anomaly","anomaly_type","severity"]
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_dataset_no_null_tower_id(self):
        base = os.path.join(os.path.dirname(__file__), "..")
        df = pd.read_parquet(os.path.join(base, "data", "raw", "kpi_data.parquet"))
        assert df["tower_id"].isnull().sum() == 0

    def test_dataset_tower_count(self):
        base = os.path.join(os.path.dirname(__file__), "..")
        df = pd.read_parquet(os.path.join(base, "data", "raw", "kpi_data.parquet"))
        assert df["tower_id"].nunique() == 50

    def test_anomaly_labels_binary(self):
        base = os.path.join(os.path.dirname(__file__), "..")
        df = pd.read_parquet(os.path.join(base, "data", "raw", "kpi_data.parquet"))
        assert set(df["is_anomaly"].unique()).issubset({0, 1})

    def test_latency_in_valid_range(self):
        base = os.path.join(os.path.dirname(__file__), "..")
        df = pd.read_parquet(os.path.join(base, "data", "raw", "kpi_data.parquet"))
        assert df["latency_ms"].min() >= 0
        assert df["latency_ms"].max() <= 20000

    def test_packet_loss_in_range(self):
        base = os.path.join(os.path.dirname(__file__), "..")
        df = pd.read_parquet(os.path.join(base, "data", "raw", "kpi_data.parquet"))
        assert df["packet_loss_pct"].min() >= 0
        assert df["packet_loss_pct"].max() <= 100

    def test_model_files_exist(self):
        base = os.path.join(os.path.dirname(__file__), "..")
        for fname in ["random_forest.pkl","isolation_forest.pkl","scaler.pkl","feature_columns.pkl"]:
            path = os.path.join(base, "models", fname)
            assert os.path.exists(path), f"Missing model file: {fname}"

    def test_evaluation_report_exists(self):
        base = os.path.join(os.path.dirname(__file__), "..")
        path = os.path.join(base, "models", "evaluation_report.json")
        assert os.path.exists(path)

    def test_evaluation_report_f1_above_threshold(self):
        base = os.path.join(os.path.dirname(__file__), "..")
        with open(os.path.join(base, "models", "evaluation_report.json")) as f:
            report = json.load(f)
        f1 = report.get("random_forest", {}).get("f1", 0)
        assert f1 >= 0.80, f"F1 score too low: {f1}"

    def test_tower_metadata_exists(self):
        base = os.path.join(os.path.dirname(__file__), "..")
        path = os.path.join(base, "data", "raw", "tower_metadata.csv")
        assert os.path.exists(path)

    def test_tower_metadata_50_rows(self):
        base = os.path.join(os.path.dirname(__file__), "..")
        df = pd.read_csv(os.path.join(base, "data", "raw", "tower_metadata.csv"))
        assert len(df) == 50

    def test_anomaly_results_exist(self):
        base = os.path.join(os.path.dirname(__file__), "..")
        path = os.path.join(base, "data", "processed", "anomaly_results.parquet")
        assert os.path.exists(path)
