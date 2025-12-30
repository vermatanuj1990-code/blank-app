# =========================================================
# COPPER PRICE OUTLOOK – GLOBAL + INDIA (MCX IMPACT)
# 4-Day Short-Term Directional Model
# =========================================================

import streamlit as st
import yfinance as yf
import numpy as np

st.set_page_config(page_title="Copper Outlook – India (MCX)", layout="centered")

st.title("🔩 Copper Price Outlook – India (MCX)")
st.caption("Short-term directional model | 4-Day View")

# -------------------------------
# CONFIG
# -------------------------------
MCX_REFERENCE_PRICE = 720.0  # ₹/kg (adjust anytime)

# -------------------------------
# DATA FETCH
# -------------------------------
@st.cache_data(ttl=3600)
def fetch_data():
    copper = yf.download("HG=F", period="60d", progress=False)
    dxy = yf.download("DX-Y.NYB", period="60d", progress=False)
    us10y = yf.download("^TNX", period="60d", progress=False)
    usdinr = yf.download("USDINR=X", period="60d", progress=False)
    return copper, dxy, us10y, usdinr

copper, dxy, us10y, usdinr = fetch_data()

# -------------------------------
# BASIC DATA CHECK
# -------------------------------
if (
    copper.empty or dxy.empty or us10y.empty or usdinr.empty
    or len(copper) < 25
    or len(dxy) < 10
    or len(us10y) < 10
    or len(usdinr) < 10
):
    st.error("❌ Not enough market data yet. Please try later.")
    st.stop()

# -------------------------------
# GLOBAL COPPER MODEL
# -------------------------------
price = float(copper["Close"].iloc[-1])
ma5 = float(copper["Close"].rolling(5).mean().iloc[-1])
ma20 = float(copper["Close"].rolling(20).mean().iloc[-1])

momentum = (ma5 - ma20) / price
norm_momentum = momentum / 0.01

roc = (price - copper["Close"].iloc[-6]) / copper["Close"].iloc[-6]
norm_roc = roc / 0.03

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
    0.10 * usd_score +
    0.10 * rate_score
)

trading_score = float(np.clip(trading_score, -1, 1))

# -------------------------------
# 4-DAY SCORE DECAY
# -------------------------------
scores = [
    trading_score,
    trading_score * 0.70,
    trading_score * 0.50,
    trading_score * 0.35
]

labels = ["Today", "Tomorrow", "Day +2", "Day +3"]

# -------------------------------
# USDINR IMPACT
# -------------------------------
usdinr_change = (
    usdinr["Close"].iloc[-1] - usdinr["Close"].iloc[-3]
) / usdinr["Close"].iloc[-3]

usdinr_change = float(np.clip(usdinr_change, -0.003, 0.003))  # ±0.3%

# -------------------------------
# INTERPRETATION
# -------------------------------
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

# -------------------------------
# DISPLAY
# -------------------------------
for label, score in zip(labels, scores):
    bias, icon = interpret(score)

    # Global copper expected move
    global_pct = score * 1.2  # ~1.2% max swing model
    mcx_pct = global_pct + usdinr_change
    mcx_rupees = mcx_pct * MCX_REFERENCE_PRICE

    confidence = int(abs(score) * 100)

    st.markdown(
        f"""
### {icon} {label}
**Global Bias:** {bias}  
**Confidence:** {confidence}%  

**Estimated MCX Impact (from global factors):**  
• **{mcx_pct:+.2%}**  
• **₹{mcx_rupees:+.2f} / kg**

**Drivers:**  
• Global copper momentum  
• USDINR movement  
"""
    )

st.divider()
st.caption("Note: MCX impact is derived from global copper & USDINR. No direct MCX price feed is used.")
