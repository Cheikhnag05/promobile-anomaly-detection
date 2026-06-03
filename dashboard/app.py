"""
dashboard/app.py
Promobile Network Anomaly Detection — 5-page Streamlit dashboard.
Pages: Overview | Live Feed | Tower Map | Deep Dive | Model Insights
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import joblib, os, json
from datetime import datetime, timedelta

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Promobile NOC Dashboard",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE   = os.path.join(os.path.dirname(__file__), "..")
RAW    = os.path.join(BASE, "data", "raw",       "kpi_data.parquet")
PROC   = os.path.join(BASE, "data", "processed", "anomaly_results.parquet")
META   = os.path.join(BASE, "data", "raw",       "tower_metadata.csv")
STATS  = os.path.join(BASE, "data", "raw",       "dataset_stats.json")
EVAL   = os.path.join(BASE, "models",            "evaluation_report.json")
FIMPT  = os.path.join(BASE, "models",            "feature_importance.csv")

# ── Color palette ─────────────────────────────────────────────────────────────
C_GREEN  = "#1D9E75"
C_AMBER  = "#EF9F27"
C_RED    = "#E24B4A"
C_BLUE   = "#378ADD"
C_DARK   = "#0E1E3A"
C_BG     = "#F8F9FB"

SEV_COLORS = {"none":"#1D9E75","low":"#63C132","medium":"#EF9F27","high":"#E8593C","critical":"#E24B4A"}

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 600; }
[data-testid="stMetricLabel"] { font-size: 0.85rem !important; color: #6B7280; }
.stMetric { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px;
            padding: 1rem 1.25rem; }
.block-container { padding-top: 1.5rem; }
h1 { color: #0E1E3A; font-weight: 700; }
h2, h3 { color: #1A3260; }
.sidebar-title { font-size: 1.1rem; font-weight: 600; color: #0E1E3A; margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ── Data loaders ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_results():
    if not os.path.exists(PROC): return pd.DataFrame()
    df = pd.read_parquet(PROC)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

@st.cache_data(ttl=300)
def load_meta():
    if not os.path.exists(META): return pd.DataFrame()
    return pd.read_csv(META)

@st.cache_data(ttl=3600)
def load_sample_kpi(n_per_tower=2000):
    if not os.path.exists(RAW): return pd.DataFrame()
    df = pd.read_parquet(RAW)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    sample = df.groupby("tower_id").apply(
        lambda x: x.sort_values("timestamp").tail(n_per_tower)
    ).reset_index(drop=True)
    return sample

@st.cache_data
def load_eval():
    if not os.path.exists(EVAL): return {}
    with open(EVAL) as f: return json.load(f)

@st.cache_data
def load_stats():
    if not os.path.exists(STATS): return {}
    with open(STATS) as f: return json.load(f)

@st.cache_data
def load_feature_importance():
    if not os.path.exists(FIMPT): return pd.DataFrame()
    return pd.read_csv(FIMPT)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">📡 Promobile NOC</div>', unsafe_allow_html=True)
    st.caption("Network Operations Center — Dakar, Senegal")
    st.divider()

    page = st.radio(
        "Navigation",
        ["🏠 Executive Overview", "⚡ Live Anomaly Feed",
         "🗺️ Tower Map", "🔬 Deep Dive", "🧠 Model Insights"],
        label_visibility="collapsed",
    )
    st.divider()

    stats = load_stats()
    if stats:
        st.metric("Total records", f"{stats.get('total_rows',0):,}")
        st.metric("Towers monitored", stats.get("towers", 50))
        st.metric("Anomaly rate", f"{stats.get('anomaly_rate_pct',0):.2f}%")
    st.divider()
    st.caption(f"Last refresh: {datetime.now().strftime('%H:%M:%S')}")
    if st.button("🔄 Refresh data"):
        st.cache_data.clear()
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — EXECUTIVE OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Executive Overview":
    st.title("📡 Promobile Network Operations Center")
    st.caption("Real-time anomaly detection across 50 cell towers — Senegal · Jan–Dec 2024")
    st.divider()

    results = load_results()
    meta    = load_meta()
    evl     = load_eval()

    if results.empty:
        st.warning("No results found. Run `python src/train_model.py` first.")
        st.stop()

    anom = results[results["is_anomaly_true"] == 1]
    total_anom   = len(anom)
    total_rec    = len(results)
    anom_rate    = total_anom / total_rec * 100
    critical     = len(anom[anom["severity"] == "critical"])
    high_sev     = len(anom[anom["severity"] == "high"])
    rf_f1        = evl.get("random_forest", {}).get("f1", 0)

    # ── KPI tiles ──────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Records Analysed", f"{total_rec:,}")
    c2.metric("Anomalies Detected",     f"{total_anom:,}", delta=f"{anom_rate:.2f}% of records")
    c3.metric("Critical Alerts",         f"{critical:,}",  delta_color="inverse", delta=f"{critical/total_anom*100:.1f}% of anomalies")
    c4.metric("High Severity",           f"{high_sev:,}")
    c5.metric("Model F1 Score",          f"{rf_f1:.4f}")

    st.divider()

    # ── Row 1: severity breakdown + anomaly type breakdown ─────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Anomaly severity breakdown")
        sev_counts = anom["severity"].value_counts().reset_index()
        sev_counts.columns = ["severity","count"]
        sev_order = ["critical","high","medium","low"]
        sev_counts["severity"] = pd.Categorical(sev_counts["severity"], categories=sev_order, ordered=True)
        sev_counts = sev_counts.sort_values("severity")
        fig = px.bar(sev_counts, x="severity", y="count",
                     color="severity",
                     color_discrete_map=SEV_COLORS,
                     text="count")
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False, height=320,
                          plot_bgcolor="white", paper_bgcolor="white",
                          xaxis_title="", yaxis_title="Count")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Anomaly type distribution")
        if "anomaly_type" in anom.columns:
            type_counts = anom[anom["anomaly_type"] != "normal"]["anomaly_type"].value_counts().reset_index()
            type_counts.columns = ["type","count"]
            fig = px.pie(type_counts, names="type", values="count",
                         color_discrete_sequence=px.colors.qualitative.Set2,
                         hole=0.45)
            fig.update_layout(height=320, paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)

    # ── Row 2: anomalies over time ─────────────────────────────────────────
    st.subheader("Anomaly volume over time (2024)")
    anom_time = anom.copy()
    anom_time["month"] = anom_time["timestamp"].dt.to_period("M").astype(str)
    monthly = anom_time.groupby(["month","severity"]).size().reset_index(name="count")
    fig = px.bar(monthly, x="month", y="count", color="severity",
                 color_discrete_map=SEV_COLORS, barmode="stack")
    fig.update_layout(height=320, plot_bgcolor="white", paper_bgcolor="white",
                      xaxis_title="Month", yaxis_title="Anomalies",
                      legend_title="Severity")
    st.plotly_chart(fig, use_container_width=True)

    # ── Row 3: top towers by anomaly count ────────────────────────────────
    st.subheader("Top 10 towers by anomaly count")
    tower_anom = anom.groupby("tower_id").size().reset_index(name="anomalies")
    if not meta.empty:
        tower_anom = tower_anom.merge(meta[["tower_id","district","tower_type"]], on="tower_id", how="left")
    tower_anom = tower_anom.sort_values("anomalies", ascending=False).head(10)
    fig = px.bar(tower_anom, x="tower_id", y="anomalies",
                 color="anomalies", color_continuous_scale="Reds",
                 text="anomalies",
                 hover_data=["district","tower_type"] if "district" in tower_anom.columns else None)
    fig.update_traces(textposition="outside")
    fig.update_layout(height=340, plot_bgcolor="white", paper_bgcolor="white",
                      xaxis_title="Tower ID", yaxis_title="Anomalies",
                      showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — LIVE ANOMALY FEED
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚡ Live Anomaly Feed":
    st.title("⚡ Live Anomaly Feed")
    st.caption("Most recent anomaly detections across the Senegal network")
    st.divider()

    results = load_results()
    if results.empty:
        st.warning("No results found."); st.stop()

    anom = results[results["is_anomaly_true"] == 1].copy()
    anom = anom.sort_values("timestamp", ascending=False)

    # ── Filters ────────────────────────────────────────────────────────────
    fc1, fc2, fc3 = st.columns(3)
    sev_filter  = fc1.multiselect("Severity", ["critical","high","medium","low"], default=["critical","high"])
    type_filter = fc2.multiselect("Anomaly type",
                                  sorted(anom["anomaly_type"].unique().tolist()),
                                  default=[])
    n_show      = fc3.slider("Rows to show", 20, 500, 100, step=20)

    filtered = anom.copy()
    if sev_filter:  filtered = filtered[filtered["severity"].isin(sev_filter)]
    if type_filter: filtered = filtered[filtered["anomaly_type"].isin(type_filter)]
    filtered = filtered.head(n_show)

    # ── Summary chips ──────────────────────────────────────────────────────
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Showing", f"{len(filtered):,}")
    m2.metric("Critical", len(filtered[filtered["severity"]=="critical"]))
    m3.metric("High",     len(filtered[filtered["severity"]=="high"]))
    if "rf_prob" in filtered.columns:
        m4.metric("Avg anomaly prob", f"{filtered['rf_prob'].mean():.3f}")

    st.divider()

    # ── Color-coded table ──────────────────────────────────────────────────
    def color_severity(val):
        colors = {"critical":"#fee2e2","high":"#fef3c7","medium":"#fef9c3","low":"#dcfce7","none":"white"}
        return f"background-color: {colors.get(val, 'white')}"

    display_cols = ["timestamp","tower_id","anomaly_type","severity"]
    if "rf_prob" in filtered.columns:
        display_cols.append("rf_prob")
    if "if_score" in filtered.columns:
        display_cols.append("if_score")

    styled = filtered[display_cols].style.map(color_severity, subset=["severity"])
    st.dataframe(styled, use_container_width=True, height=480)

    # ── Hourly heatmap ────────────────────────────────────────────────────
    st.subheader("Anomaly heatmap — hour of day vs day of week")
    anom["hour"] = anom["timestamp"].dt.hour
    anom["dow"]  = anom["timestamp"].dt.day_name()
    heatmap = anom.groupby(["dow","hour"]).size().reset_index(name="count")
    dow_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    heatmap["dow"] = pd.Categorical(heatmap["dow"], categories=dow_order, ordered=True)
    pivot = heatmap.pivot(index="dow", columns="hour", values="count").fillna(0)
    fig = px.imshow(pivot, color_continuous_scale="YlOrRd",
                    labels=dict(x="Hour of Day", y="Day", color="Anomalies"),
                    aspect="auto")
    fig.update_layout(height=320, paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — TOWER MAP
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🗺️ Tower Map":
    st.title("🗺️ Cell Tower Health Map — Senegal")
    st.caption("Geographic view of network anomaly density across all 50 towers")
    st.divider()

    meta    = load_meta()
    results = load_results()

    if meta.empty:
        st.warning("Tower metadata not found."); st.stop()

    # compute anomaly count + rate per tower
    if not results.empty:
        anom_counts = (results[results["is_anomaly_true"]==1]
                       .groupby("tower_id").size().reset_index(name="anomaly_count"))
        total_counts = results.groupby("tower_id").size().reset_index(name="total")
        tower_stats  = meta.merge(anom_counts, on="tower_id", how="left")
        tower_stats  = tower_stats.merge(total_counts, on="tower_id", how="left")
        tower_stats["anomaly_count"] = tower_stats["anomaly_count"].fillna(0).astype(int)
        tower_stats["total"]         = tower_stats["total"].fillna(1)
        tower_stats["anomaly_rate"]  = (tower_stats["anomaly_count"] / tower_stats["total"] * 100).round(2)
        tower_stats["health_status"] = pd.cut(
            tower_stats["anomaly_rate"],
            bins=[-1, 1.0, 1.8, 2.5, 100],
            labels=["Healthy","Warning","Alert","Critical"]
        )
    else:
        tower_stats = meta.copy()
        tower_stats["anomaly_count"] = 0
        tower_stats["anomaly_rate"]  = 0.0
        tower_stats["health_status"] = "Healthy"

    color_map = {"Healthy": C_GREEN, "Warning": C_AMBER, "Alert": "#E8593C", "Critical": C_RED}

    # ── Map ────────────────────────────────────────────────────────────────
    fig = px.scatter_mapbox(
        tower_stats,
        lat="latitude", lon="longitude",
        color="health_status",
        color_discrete_map=color_map,
        size="anomaly_count",
        size_max=25,
        hover_name="tower_id",
        hover_data={"district":True,"tower_type":True,
                    "anomaly_count":True,"anomaly_rate":True,
                    "latitude":False,"longitude":False},
        zoom=5.5,
        center={"lat": 14.5, "lon": -14.5},
        mapbox_style="open-street-map",
        title="Tower health status",
        height=550,
    )
    fig.update_layout(paper_bgcolor="white", margin=dict(l=0,r=0,t=40,b=0))
    st.plotly_chart(fig, use_container_width=True)

    # ── Status summary ─────────────────────────────────────────────────────
    st.subheader("Tower status summary")
    if "health_status" in tower_stats.columns:
        status_counts = tower_stats["health_status"].value_counts().reset_index()
        status_counts.columns = ["status","towers"]
        c1,c2,c3,c4 = st.columns(4)
        for col, status in zip([c1,c2,c3,c4],["Healthy","Warning","Alert","Critical"]):
            n = int(status_counts[status_counts["status"]==status]["towers"].sum())
            col.metric(status, n)

    # ── District breakdown ────────────────────────────────────────────────
    st.subheader("Anomaly rate by district (top 20)")
    top_dist = tower_stats.sort_values("anomaly_rate", ascending=False).head(20)
    fig2 = px.bar(top_dist, x="district", y="anomaly_rate",
                  color="health_status", color_discrete_map=color_map,
                  text="anomaly_rate")
    fig2.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig2.update_layout(height=360, plot_bgcolor="white", paper_bgcolor="white",
                       xaxis_tickangle=-45, xaxis_title="", yaxis_title="Anomaly rate (%)")
    st.plotly_chart(fig2, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — DEEP DIVE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔬 Deep Dive":
    st.title("🔬 Tower Deep Dive")
    st.caption("Per-tower time-series analysis with anomaly overlay")
    st.divider()

    kpi_df  = load_sample_kpi(n_per_tower=3000)
    results = load_results()
    meta    = load_meta()

    if kpi_df.empty:
        st.warning("KPI data not found."); st.stop()

    towers   = sorted(kpi_df["tower_id"].unique().tolist())
    sel_tower = st.selectbox("Select tower", towers)

    KPI_OPTIONS = {
        "Latency (ms)":         "latency_ms",
        "Packet loss (%)":      "packet_loss_pct",
        "Signal strength (dBm)":"signal_strength_dbm",
        "Call drop rate":       "call_drop_rate",
        "Throughput (Mbps)":    "throughput_mbps",
        "Active users":         "active_users",
        "Interference ratio":   "interference_ratio",
        "Availability (%)":     "availability_pct",
    }
    sel_kpi_label = st.selectbox("Select KPI", list(KPI_OPTIONS.keys()))
    sel_kpi       = KPI_OPTIONS[sel_kpi_label]

    tower_kpi  = kpi_df[kpi_df["tower_id"] == sel_tower].sort_values("timestamp")
    tower_anom = pd.DataFrame()
    if not results.empty:
        tower_anom = results[
            (results["tower_id"] == sel_tower) & (results["is_anomaly_true"] == 1)
        ].copy()

    if not meta.empty:
        info = meta[meta["tower_id"] == sel_tower].iloc[0]
        ic1,ic2,ic3,ic4 = st.columns(4)
        ic1.metric("Tower",   sel_tower)
        ic2.metric("District",info["district"])
        ic3.metric("Type",    info["tower_type"])
        ic4.metric("Capacity",f"{info['capacity_users']:,} users")
        st.divider()

    # ── KPI time-series with anomaly overlay ──────────────────────────────
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tower_kpi["timestamp"], y=tower_kpi[sel_kpi],
        mode="lines", name=sel_kpi_label,
        line=dict(color=C_BLUE, width=1.2),
    ))

    # rolling mean
    roll = tower_kpi[sel_kpi].rolling(48, min_periods=1).mean()
    fig.add_trace(go.Scatter(
        x=tower_kpi["timestamp"], y=roll,
        mode="lines", name="48-pt rolling mean",
        line=dict(color=C_AMBER, width=2, dash="dash"),
    ))

    # anomaly markers
    if not tower_anom.empty and sel_kpi in tower_kpi.columns:
        anom_ts = pd.to_datetime(tower_anom["timestamp"])
        merged = pd.merge_asof(
            tower_anom.sort_values("timestamp"),
            tower_kpi[["timestamp", sel_kpi]].sort_values("timestamp"),
            on="timestamp", direction="nearest"
        )
        sev_marker_colors = {
            "critical": C_RED, "high": "#E8593C",
            "medium": C_AMBER, "low": C_GREEN, "none": "gray"
        }
        for sev, grp in merged.groupby("severity"):
            fig.add_trace(go.Scatter(
                x=grp["timestamp"], y=grp[sel_kpi],
                mode="markers", name=f"Anomaly ({sev})",
                marker=dict(color=sev_marker_colors.get(sev, "gray"),
                            size=8, symbol="x"),
            ))

    fig.update_layout(
        height=400, plot_bgcolor="white", paper_bgcolor="white",
        xaxis_title="Time", yaxis_title=sel_kpi_label,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── KPI distribution: normal vs anomaly ────────────────────────────────
    st.subheader(f"Distribution — {sel_kpi_label} (normal vs anomaly)")
    normal_vals = tower_kpi[tower_kpi["is_anomaly"] == 0][sel_kpi].dropna()
    anom_vals   = tower_kpi[tower_kpi["is_anomaly"] == 1][sel_kpi].dropna()

    fig2 = go.Figure()
    fig2.add_trace(go.Histogram(x=normal_vals, name="Normal",
                                marker_color=C_BLUE, opacity=0.6, nbinsx=60))
    fig2.add_trace(go.Histogram(x=anom_vals,   name="Anomaly",
                                marker_color=C_RED,  opacity=0.7, nbinsx=60))
    fig2.update_layout(barmode="overlay", height=300,
                       plot_bgcolor="white", paper_bgcolor="white",
                       xaxis_title=sel_kpi_label, yaxis_title="Count")
    st.plotly_chart(fig2, use_container_width=True)

    # ── Correlation heatmap ────────────────────────────────────────────────
    st.subheader("KPI correlation matrix")
    kpi_numeric = ["latency_ms","packet_loss_pct","signal_strength_dbm",
                   "call_drop_rate","throughput_mbps","active_users",
                   "interference_ratio","availability_pct"]
    corr = tower_kpi[kpi_numeric].corr().round(2)
    fig3 = px.imshow(corr, color_continuous_scale="RdBu_r",
                     zmin=-1, zmax=1, text_auto=True, aspect="auto")
    fig3.update_layout(height=400, paper_bgcolor="white")
    st.plotly_chart(fig3, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — MODEL INSIGHTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🧠 Model Insights":
    st.title("🧠 Model Insights")
    st.caption("Random Forest + Isolation Forest evaluation metrics and explainability")
    st.divider()

    evl  = load_eval()
    fimp = load_feature_importance()

    if not evl:
        st.warning("Evaluation report not found. Run train_model.py first."); st.stop()

    rf  = evl.get("random_forest", {})
    ifo = evl.get("isolation_forest", {})

    # ── Model metrics ──────────────────────────────────────────────────────
    st.subheader("Model performance comparison")
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("RF Precision",  f"{rf.get('precision',0):.4f}")
    mc2.metric("RF Recall",     f"{rf.get('recall',0):.4f}")
    mc3.metric("RF F1 Score",   f"{rf.get('f1',0):.4f}")
    mc4.metric("RF ROC-AUC",    f"{rf.get('roc_auc',0):.4f}")

    st.divider()
    ic1, ic2, ic3 = st.columns(3)
    ic1.metric("IF Precision", f"{ifo.get('precision',0):.4f}")
    ic2.metric("IF Recall",    f"{ifo.get('recall',0):.4f}")
    ic3.metric("IF F1",        f"{ifo.get('f1',0):.4f}")

    st.divider()

    # ── Radar chart — model comparison ─────────────────────────────────────
    st.subheader("Model performance radar")
    categories = ["Precision","Recall","F1 Score"]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[rf.get("precision",0), rf.get("recall",0), rf.get("f1",0)],
        theta=categories, fill="toself", name="Random Forest",
        line_color=C_BLUE,
    ))
    fig.add_trace(go.Scatterpolar(
        r=[ifo.get("precision",0), ifo.get("recall",0), ifo.get("f1",0)],
        theta=categories, fill="toself", name="Isolation Forest",
        line_color=C_AMBER,
    ))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,1])),
                      showlegend=True, height=380, paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

    # ── Feature importance ──────────────────────────────────────────────────
    st.subheader("Top 20 feature importances (Random Forest)")
    if not fimp.empty:
        fimp_top = fimp.head(20).sort_values("importance")
        fig2 = px.bar(fimp_top, x="importance", y="feature",
                      orientation="h", color="importance",
                      color_continuous_scale="Blues",
                      text="importance")
        fig2.update_traces(texttemplate="%{text:.4f}", textposition="outside")
        fig2.update_layout(height=580, plot_bgcolor="white", paper_bgcolor="white",
                           yaxis_title="", xaxis_title="Importance",
                           showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Anomaly probability distribution ───────────────────────────────────
    results = load_results()
    if not results.empty and "rf_prob" in results.columns:
        st.subheader("Anomaly probability score distribution")
        fig3 = go.Figure()
        fig3.add_trace(go.Histogram(
            x=results[results["is_anomaly_true"]==0]["rf_prob"],
            name="True Normal", marker_color=C_BLUE, opacity=0.65, nbinsx=50
        ))
        fig3.add_trace(go.Histogram(
            x=results[results["is_anomaly_true"]==1]["rf_prob"],
            name="True Anomaly", marker_color=C_RED, opacity=0.7, nbinsx=50
        ))
        fig3.add_vline(x=0.5, line_dash="dash", line_color=C_DARK,
                       annotation_text="Decision boundary (0.5)")
        fig3.update_layout(barmode="overlay", height=340,
                           plot_bgcolor="white", paper_bgcolor="white",
                           xaxis_title="Anomaly probability", yaxis_title="Count")
        st.plotly_chart(fig3, use_container_width=True)

    # ── About ───────────────────────────────────────────────────────────────
    st.divider()
    with st.expander("About this project"):
        st.markdown("""
**Promobile Network Anomaly Detection System**

Built as a portfolio project inspired by real-world experience at **Promobile, Dakar** (2025),
where I designed SQL pipelines processing 8M+ rows/day and Python anomaly detection scripts
that reduced network resolution time by 30%.

**Dataset:** 8,000,000 rows · 50 cell towers · 8 KPI metrics · Jan–Dec 2024 (simulated)

**Models:**
- Isolation Forest (unsupervised baseline)
- Random Forest Classifier (supervised, class-balanced)

**Stack:** Python · pandas · scikit-learn · FastAPI · Streamlit · Plotly · Parquet

**Author:** Cheikhna Dieng Gueye · [linkedin.com/in/cheikhnagueye](https://linkedin.com/in/cheikhnagueye)
        """)
