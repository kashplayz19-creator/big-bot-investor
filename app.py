import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import google.generativeai as genai
from curl_cffi import requests
from datetime import datetime

# --- 1. STEALTH & THEME ---
stealth_session = requests.Session(impersonate="chrome124")

st.set_page_config(page_title="NEXUS | THE VAULT", page_icon="💰", layout="wide")

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=JetBrains+Mono&display=swap');
    .stApp {{ background-color: #0F0F12; color: #E0E0E0; font-family: 'Inter', sans-serif; }}
    .gold-glow {{ color: #F9D342; text-shadow: 0 0 15px rgba(249, 211, 66, 0.4); font-weight: 800; }}
    .vault-card {{ background: linear-gradient(145deg, #16181D, #0F1014); border: 1px solid #2D2F36; border-radius: 12px; padding: 20px; margin-bottom: 15px; }}
    .shadow-card {{ background: rgba(255, 255, 255, 0.02); border: 1px dotted #808080; border-radius: 12px; padding: 15px; margin-bottom: 10px; }}
    .stButton>button {{ background-color: transparent; border: 1px solid #F9D342; color: #F9D342; border-radius: 5px; transition: 0.3s; width: 100%; }}
    .stButton>button:hover {{ background-color: #F9D342; color: #0F0F12; box-shadow: 0 0 20px rgba(249, 211, 66, 0.4); }}
    .stTabs [aria-selected="true"] {{ color: #F9D342 !important; border-bottom-color: #F9D342 !important; }}
</style>
""", unsafe_allow_html=True)

# --- 2. PERSISTENCE ---
if "portfolio" not in st.session_state: st.session_state.portfolio = []
if "shadow_vault" not in st.session_state: st.session_state.shadow_vault = []

# --- 3. SIDEBAR COMMANDS ---
with st.sidebar:
    st.markdown("<h2 class='gold-glow'>COMMANDS</h2>", unsafe_allow_html=True)
    
    is_shadow = st.toggle("🌙 SHADOW MODE", help="Enable to track 'fake' trades for testing.")
    
    with st.form("entry_form"):
        st.markdown("### ➕ ADD ASSET")
        t_in = st.text_input("Ticker", "TCS.NS").upper()
        s_in = st.number_input("Shares", min_value=0.1)
        p_in = st.number_input("Price (₹)", min_value=0.1)
        
        btn_label = "ADD TO SHADOW" if is_shadow else "LOCK IN VAULT"
        if st.form_submit_button(btn_label):
            asset = {"Ticker": t_in, "Shares": s_in, "Price": p_in, "Date": datetime.now().strftime("%Y-%m-%d")}
            if is_shadow:
                st.session_state.shadow_vault.append(asset)
                st.toast("Shadow Trade Active 🌑")
            else:
                st.session_state.portfolio.append(asset)
                st.toast("Vault Asset Locked 🏛️")
            st.rerun()

# --- 4. MAIN ENGINE ---
tab_term, tab_shadow, tab_stress = st.tabs(["📊 TERMINAL", "🌑 SHADOW TRADER", "🛡️ STRESS TEST"])

with tab_term:
    active = st.text_input("Global Market Search", "HDFCBANK.NS").upper()
    try:
        t_obj = yf.Ticker(active, session=stealth_session)
        df = t_obj.history(period="6mo")
        if not df.empty:
            curr = df['Close'].iloc[-1]
            st.markdown(f"## {active} | <span class='gold-glow'>₹{curr:,.2f}</span>", unsafe_allow_html=True)
            
            # Candlestick (Green/Red as requested)
            fig = go.Figure(data=[go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                increasing_line_color='#26A69A', decreasing_line_color='#EF5350'
            )])
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=450, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
    except: st.error("Connection Throttled. Stealth Mode active.")

with tab_shadow:
    st.markdown("### 🌑 Shadow Trade Performance")
    if not st.session_state.shadow_vault:
        st.info("No shadow trades active. Use the sidebar to test a ticker without spending real money.")
    else:
        for i, s in enumerate(st.session_state.shadow_vault):
            with st.container():
                st.markdown(f"""
                <div class='shadow-card'>
                    <strong>{s['Ticker']}</strong> | Entry: ₹{s['Price']} | Qty: {s['Shares']} | Date: {s['Date']}
                </div>""", unsafe_allow_html=True)

with tab_stress:
    st.markdown("### 🌪️ Stress Tester & Monte Carlo")
    # Using real portfolio for stress test
    if st.session_state.portfolio:
        tickers = [x['Ticker'] for x in st.session_state.portfolio]
        # Download combined data
        combined_df = yf.download(tickers, period="1y", session=stealth_session)['Close']
        returns = combined_df.pct_change().dropna()
        mu, sigma = returns.mean().mean(), returns.std().mean()
        
        # Sim logic
        current_val = sum([x['Shares'] * x['Price'] for x in st.session_state.portfolio])
        sims = np.random.normal(mu, sigma, (30, 1000))
        paths = current_val * (1 + sims).cumprod(axis=0)
        
        c1, c2 = st.columns([2, 1])
        with c1:
            fig_p = go.Figure()
            for i in range(10): # Plot 10 sample paths
                fig_p.add_trace(go.Scatter(y=paths[:, i], mode='lines', opacity=0.3, line=dict(color='#F9D342')))
            fig_p.update_layout(title="Monte Carlo: 10 Possible Future Paths (30D)", template="plotly_dark", showlegend=False)
            st.plotly_chart(fig_p, use_container_width=True)
        with c2:
            st.markdown("<div class='vault-card'>", unsafe_allow_html=True)
            st.markdown("<h4 class='gold-glow'>RISK VERDICT</h4>", unsafe_allow_html=True)
            st.write(f"Confidence Floor: ₹{np.percentile(paths[-1], 5):,.2f}")
            st.write(f"Probability of Profit: {len(paths[-1][paths[-1] > current_val])/10}%")
            st.markdown("</div>", unsafe_allow_html=True)

# --- FOOTER VAULT ---
st.write("---")
st.markdown("### 🏛️ THE REAL VAULT")
if st.session_state.portfolio:
    cols = st.columns(4)
    for i, s in enumerate(st.session_state.portfolio):
        with cols[i%4]:
            st.markdown(f"<div class='vault-card'><strong>{s['Ticker']}</strong><br><span class='gold-glow'>₹{s['Price']}</span></div>", unsafe_allow_html=True)
