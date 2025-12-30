# =========================================================
# COPPER PRICE OUTLOOK – GLOBAL + MCX IMPACT (INDIA)
# =========================================================

import streamlit as st
import yfinance as yf
import numpy as np

st.set_page_config(page_title="Copper Outlook – India", layout="centered")

st.title("🔩 Copper Price Outlook – India (MCX)")
st.caption("Global-driven directional model | 4-Day View")

# ---------------------------------------------------------
# DATA FETCH
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_data():
    copper = yf.download("HG=F", period="60d", progress=False)
    dxy = yf.download("DX-Y.NYB", period="60d", progress=False)
    us10y = yf.download("^TNX", period="60d", progress=False)
    return copper, dxy, us10y

copper, dxy, us10y = fetch_data()

# ---------------------------------------------------------
# BASIC VALIDATION
# ---------------------------------------------------------
if copper.empty or len(copper) < 30:
    st.error("Not enough global copper data yet.")
    st.stop()

# ---------------------------------------------------------
# GLOBAL COPPER MODEL
# ---------------------------------------------------------
price = float(copper["Close"].iloc[-1])

ma5 = float(copper["Close"].rolling(5).mean().iloc[-1])
ma20 = float(copper["Close"].rolling(20).mean().iloc[-1])

momentum = (ma5 - ma20) / price
momentum_score = np.clip(momentum / 0.01, -1, 1)

roc = (price - float(copper["Close"].iloc[-6])) / float(copper["Close"].iloc[-6])
roc_score = np.clip(roc / 0.03, -1, 1)

price_change = float(copper["Close"].iloc[-1] - copper["Close"].iloc[-2])
trend_score = 0.4 if price_change > 0 else -0.4

# USD impact
dxy_change = float(dxy["Close"].iloc[-1] - dxy["Close"].iloc[-6])
usd_score = np.clip(-dxy_change / 1.0, -0.3, 0.3)

# Rate impact
yield_change = float(us10y["Close"].iloc[-1] - us10y["Close"].iloc[-5])
rate_score = -0.2 if yield_change > 0 else 0.2

# Final global score
global_score = (
    0.30 * momentum_score +
    0.25 * roc_score +
    0.20 * trend_score +
    0.15 * usd_score +
    0.10 * rate_score
)

global_score = float(np.clip(global_score, -1, 1))

# ---------------------------------------------------------
# 4-DAY DECAY MODEL
# ---------------------------------------------------------
scores = [
    global_score,
    global_score * 0.70,
    global_score * 0.50,
    global_score * 0.35
]

labels = ["Today", "Tomorrow", "Day +2", "Day +3"]

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

# ---------------------------------------------------------
# MCX IMPACT ESTIMATION (NO MCX DATA USED)
# ---------------------------------------------------------
def mcx_impact(score, day_factor):
    """
    Converts global score to expected MCX % range
    """
    base_move = score * 1.2 * day_factor   # % impact
    low = base_move * 0.7
    high = base_move * 1.1
    return round(low, 2), round(high, 2)

day_factors = [1.0, 0.7, 0.45, 0.3]

# ---------------------------------------------------------
# DISPLAY
# ---------------------------------------------------------
for label, score, df in zip(labels, scores, day_factors):
    bias, icon = interpret(score)
    confidence = int(abs(score) * 100)

    mcx_low, mcx_high = mcx_impact(score, df)

    st.markdown(
        f"""
### {icon} {label}
**Global Bias:** {bias}  
**Confidence:** {confidence}%  
**Expected MCX Impact:** `{mcx_low}% to {mcx_high}%`
"""
    )

st.divider()

st.caption(
    "MCX impact is an estimate derived from global copper trend, USD strength, "
    "and rate environment. Not live MCX pricing."
)
