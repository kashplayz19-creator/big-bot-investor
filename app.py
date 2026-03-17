import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import google.generativeai as genai
from curl_cffi import requests
from datetime import datetime
import pytz

# --- 1. CORE ENGINE & STEALTH ---
stealth_session = requests.Session(impersonate="chrome124")
IST = pytz.timezone('Asia/Kolkata')

st.set_page_config(page_title="NEXUS | THE VAULT", page_icon="🏛️", layout="wide")

# --- 2. THE VAULT THEME (Obsidian/Gold) ---
st.markdown("""
<style>
    .stApp { background-color: #0F0F12; color: #E0E0E0; font-family: 'Inter', sans-serif; }
    .gold-glow { color: #F9D342; text-shadow: 0 0 15px rgba(249, 211, 66, 0.4); font-weight: 800; }
    .vault-card { background: #16181D; border: 1px solid #2D2F36; border-radius: 12px; padding: 20px; }
    .intelligence-box { background: rgba(249, 211, 66, 0.03); border-left: 4px solid #F9D342; padding: 20px; border-radius: 0 10px 10px 0; }
    [data-testid="stMetricValue"] { color: #F9D342 !important; font-family: 'JetBrains Mono'; }
</style>
""", unsafe_allow_html=True)

# --- 3. LOGIC MODULES ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "portfolio" not in st.session_state: st.session_state.portfolio = []

def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def verify_handshake(key):
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        model.generate_content("ping")
        return True
    except: return False

# --- 4. COMMAND CENTER ---
with st.sidebar:
    st.markdown("<h1 class='gold-glow'>COMMAND CENTER</h1>", unsafe_allow_html=True)
    if not st.session_state.authenticated:
        key_input = st.text_input("ENTER ACCESS KEY", type="password")
        if st.button("INITIATE HANDSHAKE"):
            if verify_handshake(key_input):
                st.session_state.authenticated = True
                st.session_state.api_key = key_input
                st.rerun()
            else: st.error("ACCESS DENIED: KEY INVALID")
    else:
        st.success("ACCESS GRANTED")
        st.write(f"**VAULT TIME (IST):** {datetime.now(IST).strftime('%H:%M:%S')}")

# --- 5. MAIN ENGINE ---
if st.session_state.authenticated:
    tab_term, tab_intel = st.tabs(["📊 TERMINAL", "🕵️ INTELLIGENCE"])
    
    with tab_term:
        ticker = st.text_input("ASSET SEARCH", "HDFCBANK.NS").upper()
        t = yf.Ticker(ticker, session=stealth_session)
        df = t.history(period="6mo")
        
        if not df.empty:
            rsi_val = calculate_rsi(df).iloc[-1]
            st.markdown(f"### {ticker} | <span class='gold-glow'>RSI: {rsi_val:.2f}</span>", unsafe_allow_html=True)
            
            # Gold/Obsidian Theme Chart
            fig = go.Figure(data=[go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                increasing_line_color='#F9D342', decreasing_line_color='#FF4B4B'
            )])
            fig.update_layout(template="plotly_dark", paper_bgcolor='#0F0F12', plot_bgcolor='#0F0F12', height=400)
            st.plotly_chart(fig, use_container_width=True)

    with tab_intel:
        st.markdown("### 🏛️ INTELLIGENCE SCAN")
        if st.button("RUN QUANTITATIVE ANALYSIS"):
            model = genai.GenerativeModel('gemini-1.5-flash', tools=[{"google_search_retrieval": {}}])
            prompt = f"""
            Analyze {ticker}. Current Price: {df['Close'].iloc[-1]:.2f}. Current RSI: {rsi_val:.2f}.
            If RSI < 30, classify as 'OVERSOLD/ACCUMULATE'. If RSI > 70, classify as 'OVERBOUGHT/SECURE'.
            Provide actionable levels for the Kondapur-based investor.
            Format output in a Vault Impact Table. Tone: Elite.
            """
            response = model.generate_content(prompt)
            st.markdown(f"<div class='intelligence-box'>{response.text}</div>", unsafe_allow_html=True)
