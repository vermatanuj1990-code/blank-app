# =========================================================
# COPPER PRICE OUTLOOK – INDIA (MCX SAFE VERSION)
# =========================================================

import streamlit as st
import yfinance as yf
import numpy as np

st.set_page_config(page_title="Copper Outlook – India (MCX)", layout="centered")

st.title("🔩 Copper Price Outlook – India (MCX)")
st.caption("Short-term directional model | 4-Day View")

@st.cache_data(ttl=3600)
def safe_download(symbol, period="40d"):
    try:
        df = yf.download(symbol, period=period, progress=False)
        if df is None or df.empty:
            return None
        return df
    except:
        return None

# Fetch data
copper = safe_download("HG=F")
dxy = safe_download("DX-Y.NYB")
us10y = safe_download("^TNX")
usdinr = safe_download("USDINR=X")
nifty = safe_download("^NSEI")

missing = []

for name, df in {
    "Copper": copper,
    "DXY": dxy,
    "US 10Y Yield": us10y,
    "USD/INR": usdinr,
    "NIFTY": nifty
}.items():
    if df is None or len(df) < 25:
        missing.append(name)

if copper is None or len(copper) < 25:
    st.error("❌ Copper data unavailable. Cannot run model.")
    st.stop()

if missing:
    st.warning(f"⚠️ Partial data missing: {', '.join(missing)}")

# --- GLOBAL SCORES ---
price = float(copper["Close"].iloc[-1])
ma5 = float(copper["Close"].rolling(5).mean().iloc[-1])
ma20 = float(copper["Close"].rolling(20).mean().iloc[-1])

momentum = (ma5 - ma20) / price
roc = (price - copper["Close"].iloc[-6]) / copper["Close"].iloc[-6]

global_score = 0.6 * (momentum / 0.01) + 0.4 * (roc / 0.03)

# Dollar & Rates
if dxy is not None:
    dxy_roc = (dxy["Close"].iloc[-1] - dxy["Close"].iloc[-6]) / dxy["Close"].iloc[-6]
    global_score += -0.2 * (dxy_roc / 0.01)

if us10y is not None:
    rate_trend = us10y["Close"].iloc[-1] - us10y["Close"].iloc[-5]
    global_score += -0.2 if rate_trend > 0 else 0.2

# --- INDIA ADJUSTMENT ---
india_score = 0.0
india_weight = 0.0

if usdinr is not None:
    inr_move = (usdinr["Close"].iloc[-1] - usdinr["Close"].iloc[-5]) / usdinr["Close"].iloc[-5]
    india_score += -inr_move
    india_weight += 0.15

if nifty is not None:
    nifty_roc = (nifty["Close"].iloc[-1] - nifty["Close"].iloc[-6]) / nifty["Close"].iloc[-6]
    india_score += nifty_roc
    india_weight += 0.15

# Final base score
final_base = 0.7 * global_score + india_weight * india_score
final_base = float(np.clip(final_base, -1, 1))

# 4-Day decay
scores = [
    final_base,
    final_base * 0.7,
    final_base * 0.7 * 0.75,
    final_base * 0.7 * 0.75 * 0.75
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
    st.markdown(f"### {icon} {label}")
    st.markdown(f"**Bias:** {bias}")
    st.markdown(f"**Confidence:** {confidence}%")

st.divider()
st.caption("⚠️ This is a directional risk model, not price prediction.")
