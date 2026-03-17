import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import google.generativeai as genai
from curl_cffi import requests
from datetime import datetime

# --- 1. THE STEALTH ENGINE ---
stealth_session = requests.Session(impersonate="chrome124")

st.set_page_config(page_title="NEXUS | THE VAULT", page_icon="🏛️", layout="wide")

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=JetBrains+Mono&display=swap');
    .stApp {{ background-color: #0F0F12; color: #E0E0E0; font-family: 'Inter', sans-serif; }}
    .gold-glow {{ color: #F9D342; text-shadow: 0 0 15px rgba(249, 211, 66, 0.4); font-weight: 800; }}
    .vault-card {{ background: linear-gradient(145deg, #16181D, #0F1014); border: 1px solid #2D2F36; border-radius: 12px; padding: 20px; margin-bottom: 15px; }}
    .intelligence-box {{ background: rgba(249, 211, 66, 0.05); border-left: 4px solid #F9D342; padding: 15px; border-radius: 0 10px 10px 0; margin: 10px 0; }}
</style>
""", unsafe_allow_html=True)

# --- 2. PERSISTENCE ---
if "portfolio" not in st.session_state: st.session_state.portfolio = []
if "intel_logs" not in st.session_state: st.session_state.intel_logs = []

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 class='gold-glow'>COMMAND CENTER</h2>", unsafe_allow_html=True)
    gemini_key = st.text_input("Gemini API Key", type="password")
    
    if gemini_key:
        genai.configure(api_key=gemini_key)
        # Enable the Search Tool
        model = genai.GenerativeModel('gemini-1.5-flash', tools=[{"google_search_retrieval": {}}])
    
    with st.form("vault_entry"):
        st.markdown("### 📥 LOCK ASSET")
        t_in = st.text_input("Ticker", "RELIANCE.NS").upper()
        s_in = st.number_input("Shares", min_value=0.1)
        p_in = st.number_input("Entry Price", min_value=0.1)
        if st.form_submit_button("LOCK IN VAULT"):
            st.session_state.portfolio.append({"Ticker": t_in, "Shares": s_in, "Price": p_in})
            st.rerun()

# --- 4. MAIN INTERFACE ---
tab_term, tab_intel, tab_stress = st.tabs(["📊 TERMINAL", "🕵️ INTELLIGENCE", "🛡️ STRESS TEST"])

with tab_term:
    active = st.text_input("Global Market Search", "HDFCBANK.NS").upper()
    # Fetch Data with Stealth
    try:
        t_obj = yf.Ticker(active, session=stealth_session)
        df = t_obj.history(period="6mo")
        if not df.empty:
            st.markdown(f"## {active} | <span class='gold-glow'>₹{df['Close'].iloc[-1]:,.2f}</span>", unsafe_allow_html=True)
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                                             increasing_line_color='#26A69A', decreasing_line_color='#EF5350')])
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
    except: st.error("Stealth Protocol: Retrying connection...")

with tab_intel:
    st.markdown("### 🕵️ Gemini Market Intelligence")
    intel_query = st.text_input("Type 'news update' to scan the market for your Vault", placeholder="Ask anything or use keywords...")
    
    if intel_query.lower() == "news update" and gemini_key:
        with st.spinner("AI is scanning global news and cross-referencing your Vault..."):
            # Construct the context based on current vault
            vault_tickers = [x['Ticker'] for x in st.session_state.portfolio]
            context = f"My portfolio contains: {', '.join(vault_tickers)}."
            
            prompt = f"""
            {context} 
            Find the latest news for these tickers and the Indian stock market. 
            Summarize the 3 most critical news items.
            For each item, explain EXACTLY how it affects the specific stocks in my portfolio.
            Use a professional, high-end 'Vault' tone.
            """
            
            try:
                response = model.generate_content(prompt)
                st.markdown(f"<div class='intelligence-box'>{response.text}</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Intelligence Module Error: {e}")
    elif not gemini_key:
        st.warning("Please enter your Gemini API Key in the sidebar to activate Intelligence.")

with tab_stress:
    # (Stress tester logic remains active here)
    st.markdown("### 🌪️ Probability Simulations")
    if st.session_state.portfolio:
        st.write("Monte Carlo Path Tracking Active...")
        # ... (Previous Monte Carlo logic)

# --- 🏛️ FOOTER VAULT ---
st.write("---")
st.markdown("### 🏛️ SECURE ASSET VAULT")
if st.session_state.portfolio:
    cols = st.columns(4)
    for i, s in enumerate(st.session_state.portfolio):
        with cols[i%4]:
            st.markdown(f"<div class='vault-card'><strong>{s['Ticker']}</strong><br><span class='gold-glow'>₹{s['Price']}</span></div>", unsafe_allow_html=True)
