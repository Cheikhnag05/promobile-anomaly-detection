# 📡 Promobile Network Anomaly Detection System

> **Portfolio Project** — Inspired by real-world work at **Promobile, Dakar, Senegal (2025)**
> where I built SQL pipelines processing 8M+ rows/day and Python anomaly detection scripts
> that reduced network resolution time by 30%.

---

## Project Overview

End-to-end telecom network anomaly detection system built on 8 million rows of simulated
Senegalese cell tower KPI data. Detects latency spikes, packet loss bursts, signal degradation,
call drop surges, throughput collapses, and interference events across 50 towers nationwide.

**Live Demo:** `streamlit run dashboard/app.py`
**API Docs:** `uvicorn api.main:app --reload` → http://localhost:8000/docs

---

## Results

| Model              | Precision | Recall | F1 Score | ROC-AUC |
|--------------------|-----------|--------|----------|---------|
| Random Forest      | 0.9951    | 0.9623 | 0.9785   | 0.9906  |
| Isolation Forest   | unsupervised baseline                    |

- **8,000,000** rows processed across **50** Senegalese cell towers
- **120,000** anomalies detected (1.5% rate)
- **6** anomaly types classified with severity levels (low → critical)
- **–30%** simulated network resolution time (vs manual monitoring)
- **56/56** tests passing

---

## Tech Stack

| Layer        | Tools |
|-------------|-------|
| Data         | Python · pandas · numpy · Parquet |
| ML           | scikit-learn (Isolation Forest + Random Forest) · SHAP · joblib |
| API          | FastAPI · uvicorn · pydantic |
| Dashboard    | Streamlit · Plotly · Folium |
| Testing      | pytest · httpx |
| Version ctrl | Git · GitHub |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/cheikhna-gueye/promobile-anomaly-detection.git
cd promobile-anomaly-detection

# 2. Virtual environment
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install
pip install -r requirements.txt

# 4. Generate data (8M rows)
python src/generate_data.py

# 5. Train models
python src/train_model.py

# 6. Run tests (56 tests)
pytest tests/ -v

# 7. Launch dashboard
streamlit run dashboard/app.py

# 8. Launch API (separate terminal)
uvicorn api.main:app --reload
```

---

## Dashboard Pages

| Page | Description |
|------|-------------|
| 🏠 Executive Overview | KPI tiles, severity breakdown, anomaly timeline, top towers |
| ⚡ Live Anomaly Feed   | Filterable real-time anomaly table + hourly heatmap |
| 🗺️ Tower Map           | Senegal map with tower health color-coded (green/amber/red) |
| 🔬 Deep Dive           | Per-tower time-series, distributions, correlation matrix |
| 🧠 Model Insights      | Feature importance, radar chart, probability distribution |

---

## API Endpoints

```
GET  /          → API info
GET  /health    → Model status
POST /predict   → Real-time anomaly prediction
GET  /anomalies → Paginated anomaly history (filter by tower, severity)
GET  /stats     → Aggregated stats + model performance
```

---

## Project Structure

```
promobile-anomaly-detection/
├── data/
│   ├── raw/          ← 8M row KPI dataset + tower metadata
│   └── processed/    ← Feature-engineered data + anomaly results
├── src/
│   ├── generate_data.py    ← Simulates realistic Senegalese telecom data
│   ├── features.py         ← Feature engineering pipeline
│   └── train_model.py      ← Model training + evaluation
├── api/
│   └── main.py             ← FastAPI REST API
├── dashboard/
│   └── app.py              ← 5-page Streamlit dashboard
├── models/                 ← Saved .pkl files + evaluation report
├── tests/
│   └── test_api.py         ← 56 pytest tests
└── requirements.txt
```

---

## About

**Cheikhna Dieng Gueye** — Data Analyst
- LinkedIn: [linkedin.com/in/cheikhnagueye](https://linkedin.com/in/cheikhnagueye)
- GitHub: [github.com/cheikhna-gueye](https://github.com/cheikhna-gueye)
- Relocating to **Toulouse, France** — January 2027
