import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import google.generativeai as genai
from curl_cffi import requests
from datetime import datetime
import pytz

# --- 0. VAULT CONFIGURATION ---
session = requests.Session(impersonate="chrome124")
IST = pytz.timezone('Asia/Kolkata')

st.set_page_config(page_title="NEXUS | VAULT", page_icon="🏛️", layout="wide")

# --- 1. THE GATEKEEPER (SECURITY HANDSHAKE) ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False

def verify_handshake(key):
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        model.generate_content("ping")
        return True
    except:
        return False

# --- 2. TECHNICAL ANALYSIS ENGINE ---
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- 3. UI/UX THEME (OBSIDIAN & GOLD) ---
st.markdown("""
<style>
    .stApp { background-color: #0F0F12; color: #E0E0E0; font-family: 'Inter', sans-serif; }
    .gold-glow { color: #F9D342; text-shadow: 0 0 15px rgba(249, 211, 66, 0.4); }
    .vault-card { background: #16181D; border: 1px solid #2D2F36; border-radius: 12px; padding: 20px; }
</style>
""", unsafe_allow_html=True)

# --- 4. TERMINAL LOGIC ---
st.markdown("<h1 class='gold-glow'>🏛️ NEXUS | THE VAULT</h1>", unsafe_allow_html=True)
st.write(f"**VAULT TIME (IST):** {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')}")

if not st.session_state.authenticated:
    key_input = st.text_input("ENTER ACCESS KEY", type="password")
    if st.button("INITIATE HANDSHAKE"):
        if verify_handshake(key_input):
            st.session_state.authenticated = True
            st.session_state.api_key = key_input
            st.rerun()
        else:
            st.error("ACCESS DENIED: KEY INVALID")

if st.session_state.authenticated:
    # --- ACTIVE SESSION ---
    tab1, tab2 = st.tabs(["📊 TERMINAL", "🕵️ INTELLIGENCE"])
    
    with tab1:
        ticker = st.text_input("ASSET SEARCH", "RELIANCE.NS").upper()
        t = yf.Ticker(ticker, session=session)
        hist = t.history(period="6mo")
        
        if not hist.empty:
            rsi_val = calculate_rsi(hist).iloc[-1]
            st.markdown(f"### ASSET: {ticker} | RSI: {rsi_val:.2f}")
            
            # GOLD & OBSIDIAN CHART
            fig = go.Figure(data=[go.Candlestick(
                x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'],
                increasing_line_color='#F9D342', decreasing_line_color='#FF4B4B'
            )])
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor='#0F0F12',
                plot_bgcolor='#0F0F12',
                height=400,
                xaxis_rangeslider_visible=False
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown("### 🏛️ INTELLIGENCE SCAN")
        if st.button("RUN QUANTITATIVE ANALYSIS"):
            model = genai.GenerativeModel('gemini-1.5-flash')
            # Pass Data to AI
            prompt = f"""
            Analyze {ticker}. Cu
