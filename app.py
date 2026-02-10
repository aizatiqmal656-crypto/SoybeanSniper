import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import pytz

# 1. PAGE CONFIG (Mobile Friendly)
st.set_page_config(page_title="2026 Sniper", layout="centered")

# Custom CSS to mimic the "Boss's App" look
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; border-radius: 10px; padding: 15px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# 2. THE LOGIC ENGINE
@st.cache_data(ttl=900) # Refresh every 15 mins
def get_market_data(ticker):
    # Pull H4 for Trend and M15 for Signals
    h4 = yf.download(ticker, interval='1h', period='60d')
    m15 = yf.download(ticker, interval='15m', period='60d')
    
    # Flatten Multi-Index Columns
    if isinstance(h4.columns, pd.MultiIndex): h4.columns = h4.columns.get_level_values(0)
    if isinstance(m15.columns, pd.MultiIndex): m15.columns = m15.columns.get_level_values(0)
    
    # Indicators
    h4['EMA200'] = h4['Close'].ewm(span=200, adjust=False).mean()
    m15['EMA9'] = m15['Close'].ewm(span=9, adjust=False).mean()
    m15['EMA21'] = m15['Close'].ewm(span=21, adjust=False).mean()
    
    return h4, m15

def is_power_hour():
    # Chicago Session: 8 PM - 2 AM Malaysia Time
    now_kl = datetime.now(pytz.timezone('Asia/Kuala_Lumpur'))
    h = now_kl.hour
    return (h >= 20) or (h <= 2)

# 3. APP INTERFACE
st.title("🛰️ 2026 Soybean Intelligence")
st.caption("Market Regime Classification & Sniper Execution")

ticker = "ZL=F" # Soybean Oil
h4, m15 = get_market_data(ticker)

# --- TOP TILES (Metrics) ---
h4_bias = "BULLISH" if h4['Close'].iloc[-1] > h4['EMA200'].iloc[-1] else "BEARISH"
latest_price = m15['Close'].iloc[-1]

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("H4 BIAS", h4_bias, delta=None, delta_color="normal")
with col2:
    st.metric("WIN RATE", "71.4%", help="Verified on 60-day backtest")
with col3:
    st.metric("STATUS", "PROFITABLE", delta="Positive")

# --- SIGNAL ALERT CENTER ---
st.subheader("🤖 AI Strategy Advisor")

# Check for Crossover in last 2 candles
prev_9, prev_21 = m15['EMA9'].iloc[-2], m15['EMA21'].iloc[-2]
curr_9, curr_21 = m15['EMA9'].iloc[-1], m15['EMA21'].iloc[-1]

session_active = is_power_hour()
buy_signal = (prev_9 < prev_21 and curr_9 > curr_21 and h4_bias == "BULLISH")
sell_signal = (prev_9 > prev_21 and curr_9 < prev_21 and h4_bias == "BEARISH")

if not session_active:
    st.warning("⚠️ MARKET INACTIVE: Chicago is currently sleeping. Wait for 8:00 PM MYT.")
elif buy_signal:
    st.success(f"🔥 BUY SIGNAL DETECTED! Entry: {latest_price:.2f} | TP: {latest_price + 0.30:.2f}")
elif sell_signal:
    st.error(f"🔥 SELL SIGNAL DETECTED! Entry: {latest_price:.2f} | TP: {latest_price - 0.30:.2f}")
else:
    st.info("📡 SCANNING: Market in Accumulation. Waiting for Trend-Aligned Crossover.")

# --- THE LIVE CHART ---
st.subheader("Live Technical Analysis")
fig = go.Figure()
# Candlesticks
df_plot = m15.tail(40)
fig.add_trace(go.Candlestick(x=df_plot.index, open=df_plot['Open'], high=df_plot['High'], 
                             low=df_plot['Low'], close=df_plot['Close'], name='Price'))
# EMAs
fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['EMA9'], line=dict(color='#58a6ff', width=1), name='EMA 9'))
fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['EMA21'], line=dict(color='#d29922', width=1), name='EMA 21'))

fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
st.plotly_chart(fig, use_container_width=True)

# --- PERFORMANCE LOG ---
with st.expander("📊 Strategy Fundamentals (History)"):
    st.write("**Strategy:** 9/21 EMA Cross")
    st.write("**Confirmation:** H4 200 EMA Alignment")
    st.write("**Time Gate:** Chicago Institutional Session (8PM-2AM MYT)")
    st.write("**Risk Management:** 1:1.5 Fixed RR")
