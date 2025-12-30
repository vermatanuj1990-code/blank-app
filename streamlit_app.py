# =========================================================
# COPPER PRICE OUTLOOK – INDIA (MCX) | 4 DAY MODEL
# =========================================================

import streamlit as st
import yfinance as yf
import numpy as np

st.set_page_config(page_title="Copper Outlook India", layout="centered")

st.title("🔩 Copper Price Outlook – India (MCX)")
st.caption("Short-term directional model | 4-Day View")

# ---------------------------------------------------------
# DATA FETCH
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_data():
    return {
        "copper": yf.download("HG=F", period="90d"),
        "dxy": yf.download("DX-Y.NYB", period="90d"),
        "us10y": yf.download("^TNX", period="90d"),
        "usdinr": yf.download("USDINR=X", period="90d"),
        "nifty": yf.download("^NSEI", period="90d"),
    }

data = fetch_data()

# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------
for k, df in data.items():
    if df is None or len(df) < 30:
        st.error("Not enough market data yet. Please try later.")
        st.stop()

copper = data["copper"]
dxy = data["dxy"]
us10y = data["us10y"]
usdinr = data["usdinr"]
nifty = data["nifty"]

# ---------------------------------------------------------
# SAFE VALUE HELPER
# ---------------------------------------------------------
def safe(v):
    if v is None or not np.isfinite(v):
        return 0.0
    return float(v)

# ---------------------------------------------------------
# CORE CALCULATIONS
# ---------------------------------------------------------
price = safe(copper["Close"].iloc[-1])

ma5 = safe(copper["Close"].rolling(5).mean().iloc[-1])
ma20 = safe(copper["Close"].rolling(20).mean().iloc[-1])
momentum = safe((ma5 - ma20) / price) / 0.01

roc = safe((price - copper["Close"].iloc[-6]) / copper["Close"].iloc[-6]) / 0.03

price_change = safe(copper["Close"].iloc[-1] - copper["Close"].iloc[-2])
oi_score = 0.3 if price_change > 0 else -0.3

# USD Impact
dxy_roc = safe((dxy["Close"].iloc[-1] - dxy["Close"].iloc[-6]) / dxy["Close"].iloc[-6])
usd_score = -dxy_roc / 0.01

# Interest Rate Impact
yield_trend = safe(us10y["Close"].iloc[-1] - us10y["Close"].iloc[-6])
rate_score = -0.25 if yield_trend > 0 else 0.25

# INR Impact (MCX CRITICAL)
inr_roc = safe((usdinr["Close"].iloc[-1] - usdinr["Close"].iloc[-6]) / usdinr["Close"].iloc[-6])
inr_score = inr_roc / 0.01

# India Demand Proxy
nifty_roc = safe((nifty["Close"].iloc[-1] - nifty["Close"].iloc[-6]) / nifty["Close"].iloc[-6])
india_demand_score = nifty_roc / 0.02

# ---------------------------------------------------------
# FINAL TRADING SCORE (MCX WEIGHTED)
# ---------------------------------------------------------
trading_score = (
    0.22 * momentum +
    0.18 * roc +
    0.12 * oi_score +
    0.15 * usd_score +
    0.18 * inr_score +
    0.10 * india_demand_score +
    0.05 * rate_score
)

trading_score = float(np.clip(trading_score, -1, 1))

# ---------------------------------------------------------
# 4-DAY DECAY MODEL
# ---------------------------------------------------------
scores = [
    trading_score,
    trading_score * 0.70,
    trading_score * 0.50,
    trading_score * 0.35
]

# ---------------------------------------------------------
# INTERPRETATION
# ---------------------------------------------------------
def interpret(score):
    if score > 0.35:
        return "Strong Bullish", "🟢"
    elif score > 0.15:
        return "Mild Bullish", "🟢"
    elif score > -0.15:
        return "Sideways", "🟡"
    elif score > -0.35:
        return "Mild Bearish", "🔴"
    else:
        return "Strong Bearish", "🔴"

labels = ["Today", "Tomorrow", "Day +2", "Day +3"]

for label, score in zip(labels, scores):
    bias, icon = interpret(score)
    confidence = int(abs(score) * 100)
    st.markdown(f"### {icon} {label}")
    st.write(f"**Bias:** {bias}")
    st.write(f"**Confidence:** {confidence}%")
    st.divider()
