<div align="center">

# 📡 Promobile — Network Anomaly Detection

**Système de détection d'anomalies réseau en temps réel pour opérateurs télécom**

[![Live Demo](https://img.shields.io/badge/🌐_Live_Demo-Vercel-black?style=for-the-badge)](https://promobile-anomaly-detection.vercel.app)
[![API](https://img.shields.io/badge/⚡_API-Render-46E3B7?style=for-the-badge)](https://promobile-api.onrender.com/docs)
[![GitHub](https://img.shields.io/badge/GitHub-Cheikhnag05-181717?style=for-the-badge&logo=github)](https://github.com/Cheikhnag05/promobile-anomaly-detection)

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)](https://react.dev)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.9-F7931E?style=flat-square&logo=scikit-learn)](https://scikit-learn.org)
[![Tests](https://img.shields.io/badge/Tests-56%20passing-1D9E75?style=flat-square)](tests/)

> 🏆 **Projet portfolio** — inspiré d'une expérience réelle chez **Promobile, Dakar, Sénégal (2025)**  
> où j'ai construit des pipelines SQL traitant 8M+ lignes/jour et des scripts Python de détection d'anomalies  
> ayant réduit le temps de résolution réseau de **30%**.

</div>

---

## 🎯 En bref

Système **end-to-end** de surveillance de KPIs réseau télécom, capable de détecter automatiquement 6 types d'anomalies sur 50 tours au Sénégal, avec un modèle Random Forest atteignant **97.85% F1 Score** sur 8 millions d'enregistrements.

| 🔢 Donnée | Valeur |
|-----------|--------|
| Enregistrements analysés | **8 000 000** |
| Tours surveillées | **50** (Sénégal national) |
| Anomalies détectées | **120 000** (taux 1.5%) |
| Types d'anomalies | **6** (latence, pertes paquets, signal...) |
| Réduction temps résolution | **–30%** vs monitoring manuel |
| Tests automatisés | **56/56** ✅ |

---

## 🚀 Demo en ligne

| Service | URL | Description |
|---------|-----|-------------|
| 🖥️ **Dashboard** | [promobile-anomaly-detection.vercel.app](https://promobile-anomaly-detection.vercel.app) | Interface React complète |
| ⚡ **API REST** | [promobile-api.onrender.com](https://promobile-api.onrender.com) | FastAPI + prédiction temps réel |
| 📖 **API Docs** | [promobile-api.onrender.com/docs](https://promobile-api.onrender.com/docs) | Swagger UI interactif |

> ⚠️ L'API tourne sur le plan gratuit Render — la première requête peut prendre ~30 secondes si inactif depuis 15 min.

---

## 📊 Résultats des modèles

| Modèle | Précision | Rappel | F1 Score | ROC-AUC | Type |
|--------|-----------|--------|----------|---------|------|
| **Random Forest** | **99.51%** | **96.23%** | **97.85%** | **99.06%** | Supervisé |
| Isolation Forest | 100% | 1.82% | 3.58% | — | Non supervisé |

Le **Random Forest** est le modèle de production. L'Isolation Forest sert de baseline non supervisée pour la comparaison.

---

## 🛠️ Stack technique

```
┌─────────────────────────────────────────────────────────────┐
│                     ARCHITECTURE                            │
├───────────────┬─────────────────┬───────────────────────────┤
│   DATA LAYER  │    ML LAYER     │      SERVING LAYER        │
│               │                 │                           │
│  pandas       │  scikit-learn   │  FastAPI + uvicorn        │
│  numpy        │  RandomForest   │  Pydantic validation      │
│  pyarrow      │  IsolationForest│  CORS + REST endpoints    │
│  Parquet      │  StandardScaler │                           │
│               │  joblib         │  React 18 + Vite          │
│               │                 │  Tailwind CSS             │
│               │                 │  Recharts + Leaflet       │
├───────────────┴─────────────────┴───────────────────────────┤
│   DÉPLOIEMENT: GitHub → Render (API) + Vercel (Frontend)    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗂️ Structure du projet

```
promobile-anomaly-detection/
│
├── 📁 api/
│   └── main.py              ← FastAPI REST API (5 endpoints)
│
├── 📁 src/
│   ├── generate_data.py     ← Génère 8M lignes de KPIs réalistes
│   ├── features.py          ← Pipeline feature engineering (45 features)
│   └── train_model.py       ← Entraînement + évaluation des modèles
│
├── 📁 frontend/             ← Dashboard React (Vite + Tailwind)
│   └── src/
│       ├── pages/           ← 5 pages (Overview, LiveFeed, Map, Predict, Model)
│       └── components/      ← Composants réutilisables
│
├── 📁 dashboard/
│   └── app.py               ← Dashboard Streamlit alternatif (5 pages)
│
├── 📁 models/               ← Modèles entraînés (.pkl) + rapports
├── 📁 data/
│   ├── raw/                 ← KPI data + métadonnées tours
│   └── processed/           ← Données enrichies + prédictions
│
└── 📁 tests/
    └── test_api.py          ← 56 tests pytest (API + ML)
```

---

## 📡 API Reference

```
GET  /             → Informations API
GET  /health       → Statut des modèles ML
POST /predict      → Prédiction d'anomalie en temps réel
GET  /anomalies    → Historique paginé (filtre: tower_id, severity)
GET  /stats        → Statistiques agrégées + performance modèles
```

### Exemple `/predict`

```bash
curl -X POST "https://promobile-api.onrender.com/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "tower_id": "TW-001",
    "latency_ms": 2800,
    "packet_loss_pct": 15.0,
    "signal_strength_dbm": -95,
    "call_drop_rate": 0.45,
    "throughput_mbps": 5.0,
    "active_users": 4500,
    "interference_ratio": 0.8,
    "availability_pct": 91.0,
    "hour": 18,
    "is_peak": 1
  }'
```

Réponse :
```json
{
  "tower_id": "TW-001",
  "is_anomaly": true,
  "anomaly_probability": 0.9823,
  "severity": "critical",
  "dominant_kpi": "latency_ms",
  "recommendation": "Investigate backhaul congestion. Check routing tables for TW.",
  "predicted_at": "2024-06-03 14:32:11"
}
```

---

## ⚡ Lancer en local

```bash
# 1. Cloner
git clone https://github.com/Cheikhnag05/promobile-anomaly-detection.git
cd promobile-anomaly-detection

# 2. Installer les dépendances Python
pip install -r requirements.txt

# 3. Générer les données (8M lignes ~2 min)
python src/generate_data.py

# 4. Entraîner les modèles
python src/train_model.py

# 5. Lancer l'API
python -m uvicorn api.main:app --reload
# → http://localhost:8000/docs

# 6. Lancer le frontend (nouveau terminal)
cd frontend && npm install && npm run dev
# → http://localhost:5173

# 7. Lancer les tests
pytest tests/ -v  # 56/56 ✅
```

---

## 🧠 Feature Engineering

45 features construites à partir de 10 KPIs bruts :

- **Stats temporelles** : rolling mean/std sur 12, 48, 168 fenêtres
- **Z-scores** par KPI pour détection de déviance
- **Lag features** : latence/perte paquets sur t-1, t-3, t-6
- **Features cycliques** : `hour_sin`, `hour_cos` (encodage temporel)
- **Score de santé composite** : agrégation pondérée des KPIs (0–100)
- **Deltas** : variation instantanée par KPI

---

## 👤 Auteur

**Cheikhna Dieng Gueye** — Data Analyst & ML Engineer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Cheikhna_Gueye-0A66C2?style=flat-square&logo=linkedin)](https://linkedin.com/in/cheikhnagueye)
[![GitHub](https://img.shields.io/badge/GitHub-Cheikhnag05-181717?style=flat-square&logo=github)](https://github.com/Cheikhnag05)

> Expérience Data chez **Promobile, Dakar, Sénégal**  
> Maîtrise SQL · Python · Machine Learning · Dashboarding
