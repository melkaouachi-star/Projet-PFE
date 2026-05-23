"""
Streamlit dashboard - Fraud Monitoring Console.

Run with:
    streamlit run src/dashboard/app.py

The dashboard talks to the FastAPI backend exclusively over HTTP so it
can be deployed independently (e.g. on HuggingFace Spaces while the
API runs on Railway).
"""
from __future__ import annotations

import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from utils.config import get_config

CFG = get_config()
API_BASE = os.getenv("DASHBOARD_API_BASE_URL", CFG.dashboard.api_base_url).rstrip("/")

st.set_page_config(
    page_title="Real-time Fraud Detection Console",
    page_icon=":shield:",
    layout="wide",
)

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def api_get(path: str, **params):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        st.error(f"API error on GET {path}: {exc}")
        return None


def api_post(path: str, payload: dict):
    try:
        r = requests.post(f"{API_BASE}{path}", json=payload, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        st.error(f"API error on POST {path}: {exc}")
        return None


# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
st.sidebar.title("Fraud Console")
st.sidebar.caption(f"API: `{API_BASE}`")
view = st.sidebar.radio(
    "View",
    ["Live Monitoring", "Score a Transaction", "SHAP Explainer", "Analytics"],
)
refresh_sec = st.sidebar.slider("Auto-refresh (seconds)", 0, 30, CFG.dashboard.refresh_interval_seconds)
if refresh_sec > 0:
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=refresh_sec * 1000, key="auto-refresh")
    except ImportError:
        pass

# -----------------------------------------------------------------------------
# Live Monitoring
# -----------------------------------------------------------------------------
if view == "Live Monitoring":
    st.title("Live Transaction Monitoring")
    stats = api_get("/api/v1/stats") or {}
    cols = st.columns(5)
    cols[0].metric("Transactions", stats.get("transactions", 0))
    cols[1].metric("Predictions", stats.get("predictions", 0))
    cols[2].metric("BLOCKED", stats.get("blocked", 0))
    cols[3].metric("REVIEW", stats.get("review", 0))
    cols[4].metric("Alerts", stats.get("alerts", 0))

    st.subheader("Recent Predictions")
    preds = api_get("/api/v1/predictions", limit=100) or []
    if preds:
        df = pd.DataFrame(preds)
        df["created_at"] = pd.to_datetime(df["created_at"])
        df = df.sort_values("created_at", ascending=False)

        def colour_decision(val):
            if val == "BLOCKED": return "background-color:#fde0e0"
            if val == "REVIEW":  return "background-color:#fff5cc"
            return "background-color:#e7f6e7"

        st.dataframe(
            df[["created_at", "transaction_id", "model_name", "fraud_probability",
                "risk_score", "decision", "explanation"]]
              # Change simplement .applymap par .map :
    .style.map(colour_decision, subset=["decision"]),
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("No predictions yet - score a transaction to populate the table.")

    st.subheader("Active Alerts")
    alerts = api_get("/api/v1/alerts", limit=50) or []
    if alerts:
        st.dataframe(pd.DataFrame(alerts), use_container_width=True, hide_index=True)
    else:
        st.success("No active fraud alerts.")

# -----------------------------------------------------------------------------
# Score a Transaction
# -----------------------------------------------------------------------------
elif view == "Score a Transaction":
    st.title("Score a Transaction")
    with st.form("score_form"):
        c1, c2, c3 = st.columns(3)
        time_val = c1.number_input("Time (seconds since dataset start)", value=10000.0)
        amount = c2.number_input("Amount (EUR)", value=120.50, step=1.0, min_value=0.0)
        external_id = c3.text_input("External transaction id", value="manual-001")
        st.markdown("**PCA components (defaults to 0):**")
        vcols = st.columns(7)
        v_inputs = {f"V{i}": vcols[(i-1) % 7].number_input(f"V{i}", value=0.0, format="%.4f")
                    for i in range(1, 29)}
        submitted = st.form_submit_button("Score transaction", type="primary")

    if submitted:
        payload = {"Time": time_val, "Amount": amount, "external_id": external_id, **v_inputs}
        res = api_post("/api/v1/predict", payload)
        if res:
            decision = res["decision"]
            colour = {"BLOCKED": "red", "REVIEW": "orange", "APPROVED": "green"}.get(decision, "blue")
            st.markdown(f"### Decision: :{colour}[**{decision}**]")
            m1, m2, m3 = st.columns(3)
            m1.metric("Fraud probability", f"{res['fraud_probability']:.4f}")
            m2.metric("Risk score", f"{res['risk_score']}/100")
            m3.metric("Threshold", f"{res['threshold']:.2f}")
            st.write("**Explanation:**")
            for r in res["explanation"]:
                st.markdown(f"- {r}")
            st.caption(f"Model: `{res['model_name']}`  -  Stored as transaction #{res['transaction_id']}")

# -----------------------------------------------------------------------------
# SHAP Explainer
# -----------------------------------------------------------------------------
elif view == "SHAP Explainer":
    st.title("SHAP Explainer")
    st.caption("Send a synthetic transaction and inspect its SHAP decomposition.")
    with st.form("shap_form"):
        time_val = st.number_input("Time", value=10000.0)
        amount = st.number_input("Amount (EUR)", value=120.0, min_value=0.0)
        v14 = st.slider("V14 (negative values strongly correlate with fraud)", -10.0, 10.0, -3.0)
        v17 = st.slider("V17", -10.0, 10.0, -2.5)
        submitted = st.form_submit_button("Explain")

    if submitted:
        payload = {"Time": time_val, "Amount": amount, "V14": v14, "V17": v17}
        for i in range(1, 29):
            payload.setdefault(f"V{i}", 0.0)
        exp = api_post("/api/v1/explain", payload)
        if exp:
            st.subheader("Top reasons")
            for r in exp["top_reasons"]:
                st.markdown(f"- {r}")
            df = pd.DataFrame({
                "feature": exp["feature_names"],
                "shap": exp["shap_values"],
            }).sort_values("shap", key=abs, ascending=False).head(15)
            fig = px.bar(df, x="shap", y="feature", orientation="h",
                         color="shap", color_continuous_scale="RdBu_r",
                         title="Top 15 SHAP contributions")
            st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# Analytics
# -----------------------------------------------------------------------------
elif view == "Analytics":
    st.title("Fraud Analytics")
    preds = api_get("/api/v1/predictions", limit=1000) or []
    if not preds:
        st.info("No data yet - generate some predictions.")
    else:
        df = pd.DataFrame(preds)
        df["created_at"] = pd.to_datetime(df["created_at"])
        df["hour"] = df["created_at"].dt.hour

        st.subheader("Decisions over time")
        st.plotly_chart(
            px.histogram(df, x="created_at", color="decision", nbins=40,
                         title="Decision volume over time"),
            use_container_width=True,
        )

        st.subheader("Risk score distribution")
        st.plotly_chart(
            px.histogram(df, x="risk_score", color="decision", nbins=30,
                         title="Risk score distribution"),
            use_container_width=True,
        )

        st.subheader("Hourly fraud rate")
        rate = df.assign(is_fraud=(df["decision"] == "BLOCKED").astype(int))\
                 .groupby("hour")["is_fraud"].mean().reset_index()
        st.plotly_chart(px.bar(rate, x="hour", y="is_fraud",
                               title="Blocked rate by hour of day"),
                        use_container_width=True)

st.sidebar.caption(f"v{CFG.project.version}  -  {datetime.utcnow():%Y-%m-%d %H:%M UTC}")
