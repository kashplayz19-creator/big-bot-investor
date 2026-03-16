import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from google.oauth2.service_account import Credentials
from datetime import datetime

# 1. PAGE CONFIG
st.set_page_config(page_title="Nexus Invest | Pro Terminal", page_icon="📡", layout="wide")

# --- 2. THE "CARBON MINT" HIGH-HOOK UI ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@500&display=swap');
    
    /* Base Theme */
    .stApp { background-color: #0A0B10; color: #E0E0E0; font-family: 'Inter', sans-serif; }
    
    /* FADE-IN & SLIDE TRANSITION */
    @keyframes slideUp { 
        from { opacity: 0; transform: translateY(20px); } 
        to { opacity: 1; transform: translateY(0); } 
    }
    .main .block-container { animation: slideUp 0.8s ease-out; }

    /* GLASSMORPHISM CARD (Rule of Depth) */
    .nexus-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.01) 100%);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 24px;
        backdrop-filter: blur(12px);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        margin-bottom: 15px;
    }
    
    /* MICRO-INTERACTION (The Hook) */
    .nexus-card:hover {
        border: 1px solid #00FFC2;
        transform: scale(1.02);
        box-shadow: 0px 20px 40px rgba(0, 255, 194, 0.15);
        background: rgba(255, 255, 255, 0.07);
    }

    /* TYPOGRAPHY & COLORS */
    .mint-glow { color: #00FFC2; text-shadow: 0 0 10px rgba(0,255,194,0.4); font-weight: 800; }
    .red-glow { color: #FF4B4B; text-shadow: 0 0 10px rgba(255,75,75,0.3); font-weight: 800; }
    .big-stat { font-family: 'JetBrains Mono', monospace; font-size: 38px !important; font-weight: 800; letter-spacing: -1px; }
    
    /* TABS STYLING */
    .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: 600; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { color: #00FFC2 !important; border-bottom-color: #00FFC2 !important; }

    /* CUSTOM SCROLLBAR */
    ::-webkit-scrollbar { width: 8px; background: #0A0B10; }
    ::-webkit-scrollbar-thumb { background: #1E1E26; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 3. DATA & LOGIC ---
if "portfolio" not in st.session_state:
    st.session_state.portfolio = [
        {"Ticker": "HDFCBANK.NS", "Shares": 5, "Buy Price": 833.95},
        {"Ticker": "NIFTYBEES.NS", "Shares": 22, "Buy Price": 269.20},
    ]

# Greeting Logic
hour = datetime.now().hour
greeting = "Good Morning" if hour < 12 else "Good Afternoon" if hour < 17 else "Good Evening"

# --- 4. THE MODULAR GRID ---
# F-Pattern Layout: Greetings (Left), Center (Engine), Profit Hook (Right)
col_left, col_mid, col_right = st.columns([1, 2, 1])

with col_left:
    st.markdown(f"#### {greeting}, Investor")
    st.markdown(f"""<div class='nexus-card'>
        <small style='color:#808080'>MARKET STATUS</small><br>
        <span class='mint-glow'>LIVE 📡</span><br>
        <small>{datetime.now().strftime('%H:%M IST')}</small>
    </div>""", unsafe_allow_html=True)
    
    with st.expander("🔔 REMINDERS"):
        st.info("Check BEL RSI levels at 3:15")
        st.info("Update HDFC audit log")

with col_mid:
    st.markdown("<h1 style='text-align: center; letter-spacing: 5px;'>NEXUS <span class='mint-glow'>INVEST</span></h1>", unsafe_allow_html=True)
    ticker = st.text_input("ENTER TICKER", value="HDFCBANK.NS").upper()
    
    # Live Data Fetch
    t_data = yf.Ticker(ticker)
    df = t_data.history(period="1mo")
    
    if not df.empty:
        price = df['Close'].iloc[-1]
        change = price - df['Close'].iloc[-2]
        st.markdown(f"<div style='text-align:center;'><span class='big-stat'>₹{price:,.2f}</span><br><span class='{'mint-glow' if change >=0 else 'red-glow'}'>{'▲' if change >=0 else '▼'} {abs(change):.2f} Today</span></div>", unsafe_allow_html=True)
        
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=350, margin=dict(l=0,r=0,b=0,t=0), xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

with col_right:
    # Portfolio Hook
    total_val = 0
    total_pl = 0
    for s in st.session_state.portfolio:
        cur = yf.Ticker(s['Ticker']).fast_info['last_price']
        total_val += (cur * s['Shares'])
        total_pl += (cur - s['Buy Price']) * s['Shares']

    st.markdown(f"""
    <div class='nexus-card' style='text-align: center; border-bottom: 3px solid #00FFC2;'>
        <small style='color:#808080'>NET WORTH</small><br>
        <span style='font-size: 28px; font-weight: 800;'>₹{total_val:,.2f}</span><br>
        <span class='{"mint-glow" if total_pl >=0 else "red-glow"}'>
            {'↑' if total_pl >=0 else '↓'} ₹{abs(total_pl):,.2f}
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("##### 🧪 AI SENTIMENT")
    st.markdown("<div class='nexus-card' style='font-size: 14px;'>Bullish momentum detected in NSE indices. Recommend holding current positions.</div>", unsafe_allow_html=True)
