# =========================================================
# COPPER PRICE OUTLOOK APP (4 DAYS)
# =========================================================

import streamlit as st
import yfinance as yf
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Copper Outlook", layout="centered")

st.title("🔩 Copper Price Outlook")
st.caption("Short-term directional model | 4-Day View")

@st.cache_data(ttl=3600)
def fetch_data():
    copper = yf.download("HG=F", period="40d")
    dxy = yf.download("DX-Y.NYB", period="40d")
    us10y = yf.download("^TNX", period="40d")
    return copper, dxy, us10y

copper, dxy, us10y = fetch_data()

if len(copper) < 25:
    st.error("Not enough data. Please check later.")
    st.stop()

price = copper["Close"].iloc[-1]
ma5 = copper["Close"].rolling(5).mean().iloc[-1]
ma20 = copper["Close"].rolling(20).mean().iloc[-1]

momentum = (ma5 - ma20) / price
norm_momentum = momentum / 0.01

roc = (price - copper["Close"].iloc[-6]) / copper["Close"].iloc[-6]
norm_roc = roc / 0.03

avg_vol = copper["Volume"].rolling(20).mean().iloc[-1]
latest_vol = copper["Volume"].iloc[-1]

if (
    avg_vol is not None
    and latest_vol is not None
    and avg_vol > 0
    and np.isfinite(avg_vol)
    and np.isfinite(latest_vol)
):
    volume_ratio = latest_vol / avg_vol
    if np.isfinite(volume_ratio):
        norm_volume = min(volume_ratio / 2, 1)
    else:
        norm_volume = 0.0
else:
    norm_volume = 0.0

price_change = copper["Close"].iloc[-1] - copper["Close"].iloc[-2]
oi_score = 0.4 if price_change > 0 else -0.4

dxy_roc = (dxy["Close"].iloc[-1] - dxy["Close"].iloc[-6]) / dxy["Close"].iloc[-6]
usd_score = -dxy_roc / 0.01

yield_trend = us10y["Close"].iloc[-1] - us10y["Close"].iloc[-5]
rate_score = -0.3 if yield_trend > 0 else 0.3

trading_score = (
    0.30 * norm_momentum +
    0.20 * norm_roc +
    0.20 * oi_score +
    0.10 * norm_volume +
    0.10 * usd_score +
    0.10 * rate_score
)

trading_score = np.clip(trading_score, -1, 1)

inventory_score = 0.0
policy_score = 0.0

final_score = (
    0.35 * trading_score +
    0.20 * inventory_score +
    0.15 * policy_score
)

scores = [
    final_score,
    final_score * 0.65 + trading_score * 0.25,
    final_score * 0.65 * 0.75,
    final_score * 0.65 * 0.75 * 0.75
]

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
    st.markdown(f"### {icon} {label}\n**Bias:** {bias}  \n**Confidence:** {confidence}%")

st.divider()
st.caption(f"Last updated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}")
st.caption("⚠️ Directional aid only. Not financial advice.")
