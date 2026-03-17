import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import google.generativeai as genai
from curl_cffi import requests
from datetime import datetime
import pytz

# --- 0. STEALTH PROTOCOL ---
session = requests.Session(impersonate="chrome124")
IST = pytz.timezone('Asia/Kolkata')

# --- 1. UI CONFIGURATION ---
st.set_page_config(page_title="NEXUS | THE VAULT", page_icon="🏛️", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=JetBrains+Mono&display=swap');
    .stApp { background-color: #0F0F12; color: #E0E0E0; font-family: 'Inter', sans-serif; }
    .gold-glow { color: #F9D342; text-shadow: 0 0 15px rgba(249, 211, 66, 0.4); font-weight: 800; }
    .vault-card { background: #16181D; border: 1px solid #2D2F36; border-radius: 12px; padding: 20px; margin-bottom: 10px; }
    .stMetricValue { font-family: 'JetBrains Mono'; color: #F9D342 !important; }
    /* Technical Tables Styling */
    th { color: #F9D342 !important; background-color: #1A1C23 !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: transparent; border-radius: 4px 4px 0px 0px; color: #E0E0E0; }
    .stTabs [aria-selected="true"] { color: #F9D342 !important; border-bottom-color: #F9D342 !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. PERSISTENCE LAYER ---
if "portfolio" not in st.session_state: st.session_state.portfolio = {}
if "subs_cost" not in st.session_state: st.session_state.subs_cost = 600

# --- 3. COMMAND CENTER (SIDEBAR) ---
with st.sidebar:
    st.markdown("<h2 class='gold-glow'>COMMAND CENTER</h2>", unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password")
    
    # Handshake Protocol
    model_active = False
    if api_key:
        try:
            genai.configure(api_key=api_key)
            test_model = genai.GenerativeModel('gemini-1.5-flash')
            st.success("✅ ACCESS GRANTED")
            model_active = True
            model = genai.GenerativeModel('gemini-1.5-flash', tools=[{"google_search_retrieval": {}}])
        except:
            st.error("❌ ACCESS DENIED")
    
    with st.form("vault_entry"):
        st.markdown("### 📥 LOCK ASSET")
        t_in = st.text_input("Ticker (NSE)", "HDFCBANK.NS").upper()
        s_in = st.number_input("Shares", min_value=1.0, value=1.0)
        p_in = st.number_input("Entry Price (₹)", min_value=0.1, value=1500.0)
        if st.form_submit_button("LOCK IN VAULT"):
            st.session_state.portfolio[t_in] = {"shares": s_in, "entry": p_in}
            st.rerun()
    
    if st.button("RESET VAULT"):
        st.session_state.portfolio = {}
        st.rerun()

# --- 4. DATA ENGINE (RSI LOGIC) ---
def get_rsi(df, periods=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- 5. MAIN INTERFACE ---
tab1, tab2, tab3 = st.tabs(["📊 TERMINAL", "🕵️ INTELLIGENCE", "💳 LIFESTYLE YIELD"])

with tab1:
    search = st.text_input("Market Search (IST)", "NIFTYBEES.NS").upper()
    try:
        t = yf.Ticker(search, session=session)
        data = t.history(period="6mo")
        
        if not data.empty:
            curr = data['Close'].iloc[-1]
            data['RSI'] = get_rsi(data)
            current_rsi = data['RSI'].iloc[-1]
            
            col_a, col_b = st.columns([1, 2])
            with col_a:
                st.markdown(f"<div class='vault-card'><h2>{search}</h2><h1 class='gold-glow'>₹{curr:,.2f}</h1></div>", unsafe_allow_html=True)
                st.metric("RSI (14)", f"{current_rsi:.2f}", delta="OVERSOLD" if current_rsi < 30 else "OVERBOUGHT" if current_rsi > 70 else "NEUTRAL")
                st.write(f"Last Updated: {datetime.now(IST).strftime('%H:%M:%S')} IST")

            with col_b:
                fig = go.Figure(data=[go.Candlestick(
                    x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                    increasing_line_color='#F9D342', decreasing_line_color='#EF5350' # Gold for growth
                )])
                fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                height=400, margin=dict(t=0, b=0, l=0, r=0), xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
    except:
        st.error("Connection Interrupted: Check Stealth Protocol")

with tab2:
    st.markdown("### 🕵️ INTELLIGENCE PROTOCOL")
    intel_query = st.text_input("Execute Global Scan", placeholder="Search news for Vault assets...")
    
    if st.button("SCAN NETWORK") and model_active:
        with st.spinner("Analyzing Market Signals..."):
            # We pass the AI the Portfolio AND the current RSI data
            context = str(st.session_state.portfolio)
            prompt = f"""
            SYSTEM: Act as Nexus Intelligence Engine. Use Gold/Obsidian theme in responses.
            USER DATA: {context}.
            QUERY: {intel_query}.
            TASK: Search news from the last 24 hours. Analyze impact on my assets. 
            Include RSI levels and deliver a 'Vault Impact Table' with 🟢/🔴 signals.
            """
            response = model.generate_content(prompt)
            st.markdown(f"<div class='intelligence-box' style='background: #16181D; padding: 20px; border-left: 5px solid #F9D342;'>{response.text}</div>", unsafe_allow_html=True)

with tab3:
    st.markdown("### 💳 LIFESTYLE COVERAGE")
    if not st.session_state.portfolio:
        st.info("Vault is currently empty. Add assets to see coverage.")
    else:
        total_val = 0
        total_gain = 0
        
        cols = st.columns(len(st.session_state.portfolio))
        for i, (ticker, info) in enumerate(st.session_state.portfolio.items()):
            t = yf.Ticker(ticker, session=session)
            curr_p = t.history(period="1d")['Close'].iloc[-1]
            val = info['shares'] * curr_p
            gain = (curr_p - info['entry']) * info['shares']
            total_val += val
            total_gain += gain
            
            with cols[i]:
                st.markdown(f"<div class='vault-card'><strong>{ticker}</strong><br>₹{curr_p:,.2f}<br><small>Gain: ₹{gain:,.2f}</small></div>", unsafe_allow_html=True)
        
        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("Total Vault Value", f"₹{total_val:,.2f}")
        c2.metric("Total Gain/Loss", f"₹{total_gain:,.2f}", delta=f"{total_gain:.2f}")
        
        coverage_months = total_gain / st.session_state.subs_cost
        
        st.markdown(f"### <span class='gold-glow'>🟢 LIFESTYLE SECURED: {int(coverage_months)} MONTHS</span>", unsafe_allow_html=True)
        st.progress(min(max(coverage_months / 12, 0.0), 1.0))
        st.caption(f"Progress toward 1-year financial freedom (₹{st.session_state.subs_cost * 12} goal)")

st.write("---")
st.markdown(f"🏛️ **NEXUS | VAULT TERMINAL | KONDAPUR, HYDERABAD | {datetime.now(IST).strftime('%d %b %Y | %H:%M')} IST**")
