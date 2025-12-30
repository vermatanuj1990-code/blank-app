# =========================================================
# COPPER PRICE OUTLOOK – INDIA (HYBRID MCX MODEL)
# =========================================================

import streamlit as st
import yfinance as yf
import numpy as np

st.set_page_config(page_title="Copper Outlook India", layout="centered")

st.title("🔩 Copper Price Outlook – India (MCX)")
st.caption("Hybrid global + India model | 4-Day directional view")

# ---------------------------------------------------------
# FETCH GLOBAL DATA
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_data():
    copper = yf.download("HG=F", period="60d", progress=False)
    dxy = yf.download("DX-Y.NYB", period="60d", progress=False)
    us10y = yf.download("^TNX", period="60d", progress=False)
    usdinr = yf.download("USDINR=X", period="60d", progress=False)
    return copper, dxy, us10y, usdinr

copper, dxy, us10y, usdinr = fetch_data()

if len(copper) < 30 or len(usdinr) < 10:
    st.error("Not enough global market data yet. Please try later.")
    st.stop()

# ---------------------------------------------------------
# USER INPUT – MCX COPPER
# ---------------------------------------------------------
st.subheader("🇮🇳 MCX Copper Input")

mcx_price = st.number_input(
    "Enter current MCX Copper price (₹ per kg)",
    min_value=500.0,
    max_value=2000.0,
    step=1.0
)

if mcx_price == 0:
    st.warning("Please enter MCX Copper price to run India model.")
    st.stop()

# ---------------------------------------------------------
# GLOBAL CALCULATIONS
# ---------------------------------------------------------
price = float(copper["Close"].iloc[-1])

ma5 = float(copper["Close"].rolling(5).mean().iloc[-1])
ma20 = float(copper["Close"].rolling(20).mean().iloc[-1])
momentum = (ma5 - ma20) / price
momentum_score = np.clip(momentum / 0.01, -1, 1)

roc = (price - copper["Close"].iloc[-6]) / copper["Close"].iloc[-6]
roc_score = np.clip(roc / 0.03, -1, 1)

avg_vol = float(copper["Volume"].rolling(20).mean().iloc[-1])
latest_vol = float(copper["Volume"].iloc[-1])
volume_score = np.clip((latest_vol / avg_vol - 1), -1, 1) if avg_vol > 0 else 0

dxy_roc = (dxy["Close"].iloc[-1] - dxy["Close"].iloc[-6]) / dxy["Close"].iloc[-6]
usd_score = np.clip(-dxy_roc / 0.01, -1, 1)

yield_trend = us10y["Close"].iloc[-1] - us10y["Close"].iloc[-5]
rate_score = -0.3 if yield_trend > 0 else 0.3

usdinr_change = (usdinr["Close"].iloc[-1] - usdinr["Close"].iloc[-6]) / usdinr["Close"].iloc[-6]
inr_score = np.clip(usdinr_change / 0.01, -1, 1)

# ---------------------------------------------------------
# FINAL SCORE
# ---------------------------------------------------------
final_score = (
    0.25 * momentum_score +
    0.20 * roc_score +
    0.15 * volume_score +
    0.15 * usd_score +
    0.10 * rate_score +
    0.15 * inr_score
)

final_score = float(np.clip(final_score, -1, 1))

# ---------------------------------------------------------
# FORWARD DECAY (4 DAYS)
# ---------------------------------------------------------
scores = [
    final_score,
    final_score * 0.7,
    final_score * 0.5,
    final_score * 0.35
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

st.divider()

for label, score in zip(labels, scores):
    bias, icon = interpret(score)
    confidence = int(abs(score) * 100)
    st.markdown(f"### {icon} {label}")
    st.write(f"**Bias:** {bias}")
    st.write(f"**Confidence:** {confidence}%")

st.divider()
st.caption("⚠️ Directional outlook only. Not trading advice.")
