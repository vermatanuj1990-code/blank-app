import streamlit as st
import yfinance as yf
import numpy as np

st.set_page_config(page_title="Copper Outlook", layout="centered")

st.title("🔩 Copper Price Outlook")
st.caption("Short-term directional model | 4-Day View")

@st.cache_data(ttl=3600)
def fetch_close(ticker, days=60):
    data = yf.download(ticker, period=f"{days}d", progress=False)
    if data.empty or "Close" not in data:
        return None
    return data["Close"].dropna()

copper = fetch_close("HG=F")
dxy = fetch_close("DX-Y.NYB")
us10y = fetch_close("^TNX")

# ---- HARD SAFETY CHECK ----
if copper is None or dxy is None or us10y is None:
    st.error("Market data unavailable")
    st.stop()

if len(copper) < 15 or len(dxy) < 8 or len(us10y) < 8:
    st.warning("Not enough data yet")
    st.stop()

# ---- FORCE SCALARS (NO SERIES ANYWHERE) ----
price = float(copper.iloc[-1])
ma5 = float(copper.tail(5).mean())
ma20 = float(copper.tail(20).mean())

momentum = (ma5 - ma20) / price
roc = (price - float(copper.iloc[-6])) / float(copper.iloc[-6])

price_change = price - float(copper.iloc[-2])
oi_score = 0.4 if price_change > 0 else -0.4

dxy_roc = (float(dxy.iloc[-1]) - float(dxy.iloc[-6])) / float(dxy.iloc[-6])
usd_score = -dxy_roc / 0.01

yield_trend = float(us10y.iloc[-1]) - float(us10y.iloc[-5])
rate_score = -0.3 if yield_trend > 0 else 0.3

trading_score = (
    0.30 * (momentum / 0.01) +
    0.20 * (roc / 0.03) +
    0.20 * oi_score +
    0.10 * usd_score +
    0.10 * rate_score
)

trading_score = float(np.clip(trading_score, -1, 1))

# ---- 4 DAY DECAY MODEL ----
scores = [
    trading_score,
    trading_score * 0.7,
    trading_score * 0.5,
    trading_score * 0.35
]

def interpret(s):
    if s > 0.35:
        return "Strong Bullish", "🟢"
    elif s > 0.15:
        return "Mild Bullish", "🟢"
    elif s > -0.15:
        return "Sideways", "🟡"
    elif s > -0.35:
        return "Mild Bearish", "🔴"
    else:
        return "Strong Bearish", "🔴"

labels = ["Today", "Tomorrow", "Day +2", "Day +3"]

for label, s in zip(labels, scores):
    bias, icon = interpret(s)
    confidence = int(abs(s) * 100)
    st.markdown(f"### {icon} {label}")
    st.write(f"**Bias:** {bias}")
    st.write(f"**Confidence:** {confidence}%")
