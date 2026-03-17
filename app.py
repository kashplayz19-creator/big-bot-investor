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
# This impersonates a browser to prevent Yahoo Finance from blocking your Pixel 10
stealth_session = requests.Session(impersonate="chrome124")

st.set_page_config(page_title="NEXUS | THE VAULT", page_icon="🏛️", layout="wide")

# --- 2. PREMIUM CSS INJECTION ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=JetBrains+Mono&display=swap');
    
    .stApp {{
        background-color: #0F0F12;
        color: #E0E0E0;
        font-family: 'Inter', sans-serif;
    }}

    .gold-glow {{
        color: #F9D342;
        text-shadow: 0 0 15px rgba(249, 211, 66, 0.4);
        font-weight: 800;
    }}

    .vault-card {{
        background: linear-gradient(145deg, #16181D, #0F1014);
        border: 1px solid #2D2F36;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        transition: 0.3s;
    }}
    
    .intelligence-box {{
        background: rgba(249, 211, 66, 0.03);
        border-left: 4px solid #F9D342;
        padding: 20px;
        border-radius: 0 10px 10px 0;
        margin: 15px 0;
    }}

    .stButton>button {{
        background-color: transparent;
        border: 1px solid #F9D342;
        color: #F9D342;
        border-radius: 5px;
        width: 100%;
    }}
    
    .stButton>button:hover {{
        background-color: #F9D342;
        color: #0F0F12;
        box-shadow: 0 0 20px rgba(249, 211, 66, 0.4);
    }}
</style>
""", unsafe_allow_html=True)

# --- 3. PERSISTENCE & HELPERS ---
if "portfolio" not in st.session_state: st.session_state.portfolio = []
if "subs_cost" not in st.session_state: st.session_state.subs_cost = 600

def get_market_status():
    now = datetime.now()
    # IST Market Hours (approx)
    is_open = (9 <= now.hour < 16) and now.weekday() < 5
    return is_open

# --- 4. SIDEBAR (Command Center) ---
with st.sidebar:
    st.markdown("<h1 class='gold-glow'>COMMAND CENTER</h1>", unsafe_allow_html=True)
    
    gemini_key = st.text_input("Gemini API Key", type="password")
    model = None
    
    if gemini_key:
        try:
            genai.configure(api_key=gemini_key)
            # Handshake Test
            test_model = genai.GenerativeModel('gemini-1.5-flash')
            st.success("✅ ACCESS GRANTED")
            model = genai.GenerativeModel('gemini-1.5-flash', tools=[{"google_search_retrieval": {}}])
        except:
            st.error("❌ ACCESS DENIED: Check Key")
    else:
        st.warning("⚠️ VAULT LOCKED: Enter API Key")

    st.write("---")
    
    with st.form("vault_entry"):
        st.markdown("### 📥 LOCK ASSET")
        t_in = st.text_input("Ticker", "HDFCBANK.NS").upper()
        s_in = st.number_input("Shares", min_value=0.1, value=1.0)
        p_in = st.number_input("Entry Price (₹)", min_value=0.1, value=1500.0)
        if st.form_submit_button("LOCK IN VAULT"):
            st.session_state.portfolio.append({"Ticker": t_in, "Shares": s_in, "Price": p_in})
            st.toast(f"{t_in} Secured in Vault")
            st.rerun()

# --- 5. MAIN INTERFACE ---
tab_term, tab_intel, tab_stress, tab_lifestyle = st.tabs(["📊 TERMINAL", "🕵️ INTELLIGENCE", "🛡️ STRESS TEST", "💳 DIVIDENDS"])

with tab_term:
    search_ticker = st.text_input("Analyze Asset", "HDFCBANK.NS").upper()
    try:
        t_obj = yf.Ticker(search_ticker, session=stealth_session)
        df = t_obj.history(period="6mo")
        if not df.empty:
            curr_p = df['Close'].iloc[-1]
            col_a, col_b = st.columns([1, 3])
            with col_a:
                st.markdown(f"## {search_ticker}")
                st.metric("Live Price", f"₹{curr_p:,.2f}")
                status = "● LIVE" if get_market_status() else "○ SECURED"
                st.markdown(f"Status: **{status}**")
            with col_b:
                fig = go.Figure(data=[go.Candlestick(
                    x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                    increasing_line_color='#26A69A', decreasing_line_color='#EF5350'
                )])
                fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=350, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
    except:
        st.error("Stealth Protocol: Syncing...")

with tab_intel:
    st.markdown("### 🕵️ Intelligence Briefing")
    query = st.text_input("Keyword Trigger", placeholder="Type 'news update'...")
    if query and model:
        with st.spinner("Vault AI scanning global data..."):
            v_context = [x['Ticker'] for x in st.session_state.portfolio]
            prompt = f"Current Vault: {v_context}. User Query: {query}. Analyze Indian market impact in a luxury tone."
            try:
                response = model.generate_content(prompt)
                st.markdown(f"<div class='intelligence-box'>{response.text}</div>", unsafe_allow_html=True)
            except:
                st.error("Intelligence offline. Check key.")
    elif not model:
        st.info("Unlock Command Center with API Key to use Intelligence.")

with tab_stress:
    if not st.session_state.portfolio:
        st.info("Add assets to the Vault to run Stress Tests.")
    else:
        st.markdown("### 🌪️ Wealth Path Simulations")
        tickers = [x['Ticker'] for x in st.session_state.portfolio]
        # Download multiple tickers at once
        data = yf.download(tickers, period="1y", session=stealth_session)['Close']
        returns = data.pct_change().dropna()
        mu, sigma = returns.mean().mean(), returns.std().mean()
        
        current_val = sum([x['Shares'] * x['Price'] for x in st.session_state.portfolio])
        sims = np.random.normal(mu, sigma, (30, 200))
        paths = current_val * (1 + sims).cumprod(axis=0)
        
        fig_sim = go.Figure()
        for i in range(10):
            fig_sim.add_trace(go.Scatter(y=paths[:, i], mode='lines', opacity=0.4, line=dict(color='#F9D342')))
        fig_sim.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400)
        st.plotly_chart(fig_sim, use_container_width=True)
        st.write(f"Confidence Floor (Worst Case): ₹{np.percentile(paths[-1], 5):,.2f}")

with tab_lifestyle:
    st.markdown("### 💳 Subscription Coverage")
    total_div = 0
    if st.session_state.portfolio:
        for asset in st.session_state.portfolio:
            try:
                t = yf.Ticker(asset['Ticker'], session=stealth_session)
                yld = t.info.get('dividendYield', 0)
                if yld:
                    # Based on current market value
                    val = t.history(period="1d")['Close'].iloc[-1] * asset['Shares']
                    total_div += (val * yld) / 12
            except: pass
            
        st.metric("Monthly Dividend Income", f"₹{total_div:,.2f}")
        prog = min(total_div / st.session_state.subs_cost, 1.0)
        st.write(f"Lifestyle Goal: ₹{st.session_state.subs_cost}")
        st.progress(prog)
        if prog >= 1: st.success("✅ Subscription costs covered by dividends!")
    else:
        st.info("Lock assets to track dividend yield.")

# --- 6. FOOTER VAULT ---
st.write("---")
st.markdown("### 🏛️ SECURE ASSET VAULT")
if st.session_state.portfolio:
    cols = st.columns(4)
    for i, s in enumerate(st.session_state.portfolio):
        with cols[i%4]:
            st.markdown(f"<div class='vault-card'><strong>{s['Ticker']}</strong><br><span class='gold-glow'>₹{s['Price']}</span></div>", unsafe_allow_html=True)
