import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import google.generativeai as genai
from curl_cffi import requests
from datetime import datetime
import time

# --- 1. THE STEALTH ENGINE ---
# Impersonates a Chrome browser to bypass Yahoo Finance rate limits
stealth_session = requests.Session(impersonate="chrome124")

st.set_page_config(page_title="NEXUS | THE VAULT", page_icon="🏛️", layout="wide")

# --- 2. THE VAULT UI (Obsidian / Silver / Dandelion Gold) ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=JetBrains+Mono&display=swap');
    
    .stApp {{
        background-color: #0F0F12;
        color: #E0E0E0;
        font-family: 'Inter', sans-serif;
    }}

    /* Accent: Dandelion Gold Neon */
    .gold-glow {{
        color: #F9D342;
        text-shadow: 0 0 15px rgba(249, 211, 66, 0.4);
        font-weight: 800;
    }}

    /* The "Vault" Card Effect */
    .vault-card {{
        background: linear-gradient(145deg, #16181D, #0F1014);
        border: 1px solid #2D2F36;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        transition: 0.3s;
    }}
    .vault-card:hover {{
        border: 1px solid #F9D342;
        box-shadow: 0 0 20px rgba(249, 211, 66, 0.1);
    }}

    .intelligence-box {{
        background: rgba(249, 211, 66, 0.03);
        border-left: 4px solid #F9D342;
        padding: 20px;
        border-radius: 0 10px 10px 0;
        margin: 15px 0;
        font-size: 0.95rem;
        line-height: 1.6;
    }}

    /* Neon Gold Buttons */
    .stButton>button {{
        background-color: transparent;
        border: 1px solid #F9D342;
        color: #F9D342;
        border-radius: 5px;
        transition: 0.3s;
        width: 100%;
    }}
    .stButton>button:hover {{
        background-color: #F9D342;
        color: #0F0F12;
        box-shadow: 0 0 20px rgba(249, 211, 66, 0.4);
    }}

    /* Metrics Styling */
    [data-testid="stMetricValue"] {{ color: #F9D342 !important; font-family: 'JetBrains Mono'; }}
</style>
""", unsafe_allow_html=True)

# --- 3. LOGIC FUNCTIONS ---
def get_atr_stop(df, multiplier=2):
    """Calculates a volatility-based trailing stop (ATR)."""
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().iloc[-1]
    return df['Close'].iloc[-1] - (multiplier * atr)

# --- 4. SESSION STATE ---
if "portfolio" not in st.session_state: st.session_state.portfolio = []
if "shadow_vault" not in st.session_state: st.session_state.shadow_vault = []
if "subs_cost" not in st.session_state: st.session_state.subs_cost = 600 # Monthly lifestyle cost

# --- 5. SIDEBAR (Command Center) ---
with st.sidebar:
    st.markdown("<h1 class='gold-glow'>COMMAND CENTER</h1>", unsafe_allow_html=True)
    
    # API Integration
    gemini_key = st.text_input("Gemini API Key", type="password", help="Enter your key to unlock Market Intelligence.")
    if gemini_key:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-1.5-flash', tools=[{"google_search_retrieval": {}}])

    st.write("---")
    
    # Asset Entry
    is_shadow = st.toggle("🌙 SHADOW MODE", help="Test a 'hunch' trade without affecting your Real Vault.")
    
    with st.form("vault_entry"):
        st.markdown("### 📥 LOCK ASSET")
        t_in = st.text_input("Ticker (e.g., RELIANCE.NS)", "HDFCBANK.NS").upper()
        s_in = st.number_input("Shares", min_value=0.1, value=1.0)
        p_in = st.number_input("Entry Price (₹)", min_value=0.1, value=1500.0)
        
        btn_label = "ADD TO SHADOW" if is_shadow else "LOCK IN VAULT"
        if st.form_submit_button(btn_label):
            asset = {"Ticker": t_in, "Shares": s_in, "Price": p_in, "Date": datetime.now().strftime("%Y-%m-%d")}
            if is_shadow:
                st.session_state.shadow_vault.append(asset)
            else:
                st.session_state.portfolio.append(asset)
            st.rerun()

# --- 6. MAIN ENGINE TABS ---
tab_term, tab_intel, tab_stress, tab_lifestyle = st.tabs(["📊 TERMINAL", "🕵️ INTELLIGENCE", "🛡️ STRESS TEST", "💳 DIVIDENDS"])

# --- TAB 1: TERMINAL ---
with tab_term:
    search_ticker = st.text_input("Global Market Search", "HDFCBANK.NS").upper()
    try:
        t_obj = yf.Ticker(search_ticker, session=stealth_session)
        df = t_obj.history(period="6mo")
        if not df.empty:
            curr_price = df['Close'].iloc[-1]
            
            col_stat, col_chart = st.columns([1, 3])
            with col_stat:
                st.markdown(f"## {search_ticker}")
                st.metric("Live Price", f"₹{curr_price:,.2f}")
                
                # Market Status Logic
                now = datetime.now()
                is_open = (9 <= now.hour < 16) and now.weekday() < 5
                status_color = "gold-glow" if is_open else "silver"
                st.markdown(f"Status: <span class='{status_color}'>{'● LIVE' if is_open else '○ SECURED'}</span>", unsafe_allow_html=True)

            with col_chart:
                fig = go.Figure(data=[go.Candlestick(
                    x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                    increasing_line_color='#26A69A', decreasing_line_color='#EF5350'
                )])
                fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Stealth Protocol: Data sync failed. {e}")
