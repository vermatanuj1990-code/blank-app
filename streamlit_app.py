import streamlit as st
import yfinance as yf
import numpy as np

st.set_page_config(page_title="Copper Outlook", layout="centered")

st.title("🔩 Copper Price Outlook")
st.caption("Short-term directional model | 4-Day View")

@st.cache_data(ttl=3600)
def fetch():
    copper = yf.download("HG=F", period="60d", progress=False)
    dxy = yf.download("DX-Y.NYB", period="60d", progress=False)
    us10y = yf.download("^TNX", period="60d", progress=False)
    return copper.dropna(), dxy.dropna(), us10y.dropna()

copper, dxy, us10y = fetch()

if len(copper) < 30:
    st.error("Not enough market data yet")
    st.stop()

# ---- SAFE VALUES ----
price = float(copper["Close"].iloc[-1])

ma5 = float(copper["Close"].rolling(5).mean().iloc[-1])
ma20 = float(copper["Close"].rolling(20).mean().iloc[-1])

momentum = (ma5 - ma20) / price if price != 0 else 0
roc = (price - copper["Close"].iloc[-6]) / copper["Close"].iloc[-6]

dxy_roc = (dxy["Close"].iloc[-1] - dxy["Close"].iloc[-6]) / dxy["Close"].iloc[-6]
yield_change = us10y["Close"].iloc[-1] - us10y["Close"].iloc[-5]

score = (
    0.35 * np.tanh(momentum * 50) +
    0.25 * np.tanh(roc * 20) +
    0.20 * (-dxy_roc * 10) +
    0.20 * (-yield_change * 5)
)

score = np.clip(score.values[0], -1, 1) if hasattr(score, "values") else np.clip(score, -1, 1)

scores = [
    score,
    score * 0.7,
    score * 0.5,
    score * 0.35
]

labels = ["Today", "Tomorrow", "Day +2", "Day +3"]

def interpret(s):
    if s > 0.4:
        return "Strong Bullish", "🟢"
    elif s > 0.15:
        return "Mild Bullish", "🟢"
    elif s > -0.15:
        return "Sideways", "🟡"
    elif s > -0.4:
        return "Mild Bearish", "🔴"
    else:
        return "Strong Bearish", "🔴"

for l, s in zip(labels, scores):
    bias, icon = interpret(s)
    st.markdown(
        f"### {icon} {l}\n"
        f"**Bias:** {bias}  \n"
        f"**Confidence:** {int(abs(s)*100)}%"
    )

st.caption("Model: technical + USD + rates | experimental")
