import streamlit as st
import yfinance as yf
import numpy as np

st.set_page_config(page_title="Copper Outlook", layout="centered")

st.title("🔩 Copper Price Outlook")
st.caption("Short-term directional model | 4-Day View")

@st.cache_data(ttl=3600)
def fetch_close(ticker):
    df = yf.download(ticker, period="60d", progress=False)
    closes = df["Close"].dropna().values
    return closes.astype(float)

try:
    copper = fetch_close("HG=F")
    dxy = fetch_close("DX-Y.NYB")
    us10y = fetch_close("^TNX")
except Exception as e:
    st.error("Data fetch failed")
    st.stop()

if len(copper) < 15 or len(dxy) < 8 or len(us10y) < 8:
    st.error("Not enough data yet")
    st.stop()

# ---- PURE FLOAT CALCULATIONS ----
price = float(copper[-1])
ma5 = float(np.mean(copper[-5:]))
ma20 = float(np.mean(copper[-20:]))

momentum = (ma5 - ma20) / price
roc = (price - copper[-6]) / copper[-6]

price_change = price - copper[-2]
oi_score = 0.4 if price_change > 0 else -0.4

usd_roc = (dxy[-1] - dxy[-6]) / dxy[-6]
usd_score = -usd_roc

yield_trend = us10y[-1] - us10y[-5]
rate_score = -0.3 if yield_trend > 0 else 0.3

trading_score = (
    0.30 * momentum +
    0.20 * roc +
    0.20 * oi_score +
    0.15 * usd_score +
    0.15 * rate_score
)

trading_score = float(np.clip(trading_score, -1, 1))

# ---- 4 DAY DECAY ----
scores = [
    trading_score,
    trading_score * 0.75,
    trading_score * 0.55,
    trading_score * 0.40,
]

def interpret(score):
    score = float(score)
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

for label, s in zip(labels, scores):
    bias, icon = interpret(s)
    confidence = int(abs(float(s)) * 100)
    st.markdown(
        f"### {icon} {label}\n"
        f"**Bias:** {bias}  \n"
        f"**Confidence:** {confidence}%"
    )
