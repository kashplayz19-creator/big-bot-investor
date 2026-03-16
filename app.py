import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from google.oauth2.service_account import Credentials
from datetime import datetime

# 1. PAGE CONFIG
st.set_page_config(page_title="Nexus Invest | Pro Terminal", page_icon="📡", layout="wide")

# --- 2. THE ULTIMATE "CARBON MINT" CSS (UX HOOKS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@500&display=swap');
    
    .stApp { background-color: #0A0B10; color: #E0E0E0; font-family: 'Inter', sans-serif; }
    
    /* FADE-IN & SLIDE TRANSITION */
    @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    .main .block-container { animation: slideUp 0.8s ease-out; }

    /* GLASSMORPHISM CARD (The Hook) */
    .nexus-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.01) 100%);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 24px;
        backdrop-filter: blur(12px);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        margin-bottom: 15px;
    }
    .nexus-card:hover {
        border: 1px solid #00FFC2;
        transform: translateY(-5px);
        box-shadow: 0px 20px 40px rgba(0, 255, 194, 0.15);
    }

    /* TICKER TAPE ANIMATION */
    @keyframes scroll { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .ticker-wrap {
        position: fixed; bottom: 0; left: 0; width: 100%; overflow: hidden;
        background: rgba(0, 255, 194, 0.05); border-top: 1px solid rgba(0, 255, 194, 0.2);
        height: 35px; white-space: nowrap; display: flex; align-items: center; z-index: 999;
    }
    .ticker-item {
        display: inline-block; padding: 0 50px; color: #00FFC2; font-family: 'JetBrains Mono', monospace;
        font-size: 13px; animation: scroll 25s linear infinite;
    }

    .mint-glow { color: #00FFC2; text-shadow: 0 0 10px rgba(0,255,194,0.4); font-weight: 800; }
    .big-stat { font-family: 'JetBrains Mono', monospace; font-size: 38px !important; font-weight: 800; }
    
    .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: 600; }
    .stTabs [aria-selected="true"] { color: #00FFC2 !important; border-bottom-color: #00FFC2 !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. DATA PERSISTENCE ---
if "portfolio" not in st.session_state:
    st.session_state.portfolio = [
        {"Ticker": "HDFCBANK.NS", "Shares": 5, "Buy Price": 833.95},
        {"Ticker": "NIFTYBEES.NS", "Shares": 22, "Buy Price": 269.20},
    ]

# --- 4. THE MODULAR GRID ---
col_left, col_mid, col_right = st.columns([1, 2, 1])

with col_left:
    st.markdown("#### 📡 LIVE PULSE")
    st.markdown(f"""<div class='nexus-card'>
        <small style='color:#808080'>USER SESSION</small><br>
        <span class='mint-glow'>NEXUS ACTIVE</span><br>
        <small>{datetime.now().strftime('%b %d • %H:%M')}</small>
    </div>""", unsafe_allow_html=True)
    
    st.markdown("##### 📝 AUDIT LOG")
    with st.container(border=True):
        audit_t = st.text_input("Audit Ticker", "BEL.NS")
        rsi_val = st.slider("RSI Level", 0, 100, 50)
        thesis = st.text_area("Trading Thesis", placeholder="Why this trade?", height=100)
        if st.button("LOG TO DATABASE", use_container_width=True):
            st.toast("Logic saved locally!")

with col_mid:
    st.markdown("<h1 style='text-align: center; letter-spacing: 5px;'>NEXUS <span class='mint-glow'>INVEST</span></h1>", unsafe_allow_html=True)
    
    # --- UNIVERSAL SEARCH BAR ---
    query = st.text_input("🔍 SEARCH (Stock, Mutual Fund, or Index)", "HDFCBANK.NS").upper()
    
    try:
        data = yf.Ticker(query)
        df = data.history(period="1mo")
        
        if not df.empty:
            price = df['Close'].iloc[-1]
            change = price - df['Close'].iloc[-2]
            st.markdown(f"<div style='text-align:center;'><span class='big-stat'>₹{price:,.2f}</span><br><span class='{'mint-glow' if change >=0 else 'red-glow'}'>{'▲' if change >=0 else '▼'} {abs(change):.2f} Today</span></div>", unsafe_allow_html=True)
            
            # Smart Chart: Line chart for Funds, Candlestick for Stocks
            fig = go.Figure()
            if "MUTUAL" in str(data.info).upper() or "BEES" in query:
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'], line=dict(color='#00FFC2', width=2), fill='tozeroy'))
            else:
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']))
            
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=350, margin=dict(l=0,r=0,b=0,t=0), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
    except:
        st.error("Ticker not found. Try adding .NS for NSE stocks.")

with col_right:
    # Portfolio Calculation
    total_val = 0
    for s in st.session_state.portfolio:
        try:
            cur = yf.Ticker(s['Ticker']).fast_info['last_price']
            total_val += (cur * s['Shares'])
        except: pass

    st.markdown(f"""
    <div class='nexus-card' style='text-align: center; border-bottom: 3px solid #00FFC2;'>
        <small style='color:#808080'>NET WORTH</small><br>
        <span style='font-size: 28px; font-weight: 800;'>₹{total_val:,.2f}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("##### 🤖 STRATEGY CHAT")
    with st.container(border=True):
        st.chat_input("Next move?")
        st.write("<small>AI Analysis: Assets are holding strong above support levels.</small>", unsafe_allow_html=True)

# --- 5. BOTTOM ASSET VAULT ---
st.write("---")
st.markdown("### 📊 ACTIVE ASSET VAULT")
asset_cols = st.columns(len(st.session_state.portfolio))
for i, s in enumerate(st.session_state.portfolio
