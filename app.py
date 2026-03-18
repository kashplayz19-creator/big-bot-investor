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

# --- 2. THE VAULT THEME ---
st.markdown("""
<style>
    .stApp { background-color: #0F0F12; color: #E0E0E0; font-family: 'Inter', sans-serif; }
    .gold-glow { color: #F9D342; text-shadow: 0 0 15px rgba(249, 211, 66, 0.4); font-weight: 800; }
    .vault-card { background: #16181D; border: 1px solid #2D2F36; border-radius: 12px; padding: 20px; margin-bottom: 10px; }
    .intelligence-box { background: rgba(249, 211, 66, 0.05); border-left: 4px solid #F9D342; padding: 20px; border-radius: 0 10px 10px 0; }
    [data-testid="stMetricValue"] { color: #F9D342 !important; font-family: 'JetBrains Mono'; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #16181D; border-radius: 4px 4px 0 0; padding: 10px 20px; }
</style>
""", unsafe_allow_html=True)

# --- 3. LOGIC MODULES ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "portfolio" not in st.session_state: st.session_state.portfolio = {}
if "subs_cost" not in st.session_state: st.session_state.subs_cost = 600

def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / (loss + 1e-9) # Prevent division by zero
    return 100 - (100 / (1 + rs))

def verify_handshake(key):
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        model.generate_content("ping")
        return True
    except: return False

# --- 4. COMMAND CENTER (The "Master Key" Logic) ---
VAULT_PASSCODE = "1234"  # <--- Confirm this is what you want

with st.sidebar:
    st.markdown("<h1 class='gold-glow'>COMMAND CENTER</h1>", unsafe_allow_html=True)
    
    # Check if we are already logged in
    if not st.session_state.get("authenticated", False):
        input_pass = st.text_input("ENTER VAULT PASSCODE", type="password")
        
        if st.button("UNLOCK VAULT"):
            if input_pass == VAULT_PASSCODE:
                try:
                    # 1. Access the Key from Secrets
                    api_key = st.secrets["GEMINI_API_KEY"]
                    genai.configure(api_key=api_key)
                    
                    # 2. Pre-initialize the model to prevent "NotFound" errors later
                    # We store it in session_state so it stays active across tabs
                    st.session_state.model = genai.GenerativeModel(
                        model_name='gemini-1.5-flash',
                        tools=[{"google_search_retrieval": {}}]
                    )
                    
                    st.session_state.authenticated = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Intelligence Offline: {e}")
            else:
                st.error("ACCESS DENIED")
    else:
        # LOGOUT BUTTON
        if st.button("LOCK VAULT"):
            st.session_state.authenticated = False
            st.rerun()
        
        st.success("🏛️ SECURE CONNECTION")
        st.write(f"Node: Kondapur-Alpha")

        # --- ASSET LOCKER FORM ---
        with st.form("add_asset"):
            st.markdown("### 📥 LOCK ASSET")
            tick = st.text_input("Ticker", "HDFCBANK.NS").upper()
            qty = st.number_input("Shares", min_value=1.0, value=1.0)
            entry = st.number_input("Entry (₹)", min_value=1.0, value=1500.0)
            if st.form_submit_button("SECURE IN VAULT"):
                st.session_state.portfolio[tick] = {"shares": qty, "entry": entry}
                st.rerun()

# --- 5. MAIN ENGINE ---
if st.session_state.authenticated:
    tab_term, tab_intel, tab_yield = st.tabs(["📊 TERMINAL", "🕵️ INTELLIGENCE", "💳 YIELD"])
    
    with tab_term:
        ticker = st.text_input("ASSET SEARCH", "HDFCBANK.NS").upper()
        t = yf.Ticker(ticker, session=stealth_session)
        df = t.history(period="6mo")
        
        if not df.empty:
            rsi_series = calculate_rsi(df)
            rsi_val = rsi_series.iloc[-1]
            curr_p = df['Close'].iloc[-1]
            
            st.markdown(f"### {ticker} | <span class='gold-glow'>₹{curr_p:,.2f}</span>", unsafe_allow_html=True)
            st.metric("Relative Strength Index (14)", f"{rsi_val:.2f}")
            
            # Force high-contrast green/Red theme
            fig = go.Figure(data=[go.Candlestick(
                x=df.index, 
                open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                increasing_line_color='#00FF00', # green
                decreasing_line_color='#FF0000'  # Red
            )])

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)', # Transparent to match your CSS
                plot_bgcolor='rgba(0,0,0,0)',
                height=400,
                xaxis_rangeslider_visible=False,
                margin=dict(t=30, b=0, l=0, r=0),
                font=dict(color='#E0E0E0') # Force light text
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("🌐 MARKET PULSE (NSE)"):
            nifty = yf.Ticker("^NSEI", session=stealth_session)
            n_data = nifty.history(period="1d")
            if not n_data.empty:
                n_curr = n_data['Close'].iloc[-1]
                n_open = n_data['Open'].iloc[0]
                n_change = n_curr - n_open
                st.metric("NIFTY 50", f"{n_curr:,.2f}", f"{n_change:+.2f}")

   with tab_intel:
        st.markdown("### 🏛️ INTELLIGENCE SCAN")
        if st.button("RUN QUANTITATIVE ANALYSIS"):
            # Check if model exists before running
            if "model" in st.session_state:
                with st.spinner("Analyzing Global Signals..."):
                    try:
                        prompt = f"Analyze {ticker}. Price: {curr_p:.2f}, RSI: {rsi_val:.2f}. Search news (24h) and provide a Vault Impact Table."
                        # Execute using the stored session model
                        response = st.session_state.model.generate_content(prompt)
                        st.markdown(f"<div class='intelligence-box'>{response.text}</div>", unsafe_allow_html=True)
                    except Exception as ai_err:
                        st.error(f"Intelligence Protocol Failed: {ai_err}")
            else:
                st.error("Model not initialized. Please re-login at the Command Center.")

    with tab_yield:
        st.markdown("### 💳 LIFESTYLE COVERAGE")
        if not st.session_state.portfolio:
            st.info("Vault is empty. Add assets in the Command Center.")
        else:
            total_gain = 0
            cols = st.columns(len(st.session_state.portfolio))
            for i, (tick, info) in enumerate(st.session_state.portfolio.items()):
                asset_data = yf.Ticker(tick, session=stealth_session).history(period="1d")
                if not asset_data.empty:
                    c_p = asset_data['Close'].iloc[-1]
                    gain = (c_p - info['entry']) * info['shares']
                    total_gain += gain
                    with cols[i]:
                        st.markdown(f"<div class='vault-card'><strong>{tick}</strong><br>Gain: ₹{gain:,.2f}</div>", unsafe_allow_html=True)
            
            st.divider()
            coverage = total_gain / st.session_state.subs_cost
            st.metric("Total Vault Profit", f"₹{total_gain:,.2f}")
            st.markdown(f"### <span class='gold-glow'>LIFESTYLE SECURED: {int(coverage)} MONTHS</span>", unsafe_allow_html=True)
            st.progress(min(max(coverage / 12, 0.0), 1.0))

st.write("---")
st.caption("NEXUS | THE VAULT | KONDAPUR SECURE NODE")
