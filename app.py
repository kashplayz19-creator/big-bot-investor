import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import google.generativeai as genai
from curl_cffi import requests
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime

# --- 1. THE STEALTH ENGINE ---
stealth_session = requests.Session(impersonate="chrome124")

st.set_page_config(page_title="NEXUS | THE VAULT", page_icon="💰", layout="wide")

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

    /* Secondary: Slate / Silver Cards */
    .vault-card {{
        background: linear-gradient(145deg, #16181D, #0F1014);
        border: 1px solid #2D2F36;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
    }}
    
    .stButton>button {{
        background-color: transparent;
        border: 1px solid #F9D342;
        color: #F9D342;
        border-radius: 5px;
        transition: 0.3s;
    }}
    
    .stButton>button:hover {{
        background-color: #F9D342;
        color: #0F0F12;
        box-shadow: 0 0 20px rgba(249, 211, 66, 0.4);
    }}

    .stTabs [data-baseweb="tab-list"] {{ background-color: transparent; }}
    .stTabs [data-baseweb="tab"] {{ color: #C0C0C0; }}
    .stTabs [aria-selected="true"] {{ color: #F9D342 !important; border-bottom-color: #F9D342 !important; }}
</style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if "portfolio" not in st.session_state:
    st.session_state.portfolio = []

# --- 4. HEADER ---
st.markdown("<h1 class='gold-glow'>NEXUS | THE VAULT</h1>", unsafe_allow_html=True)

# --- 5. TABS ---
tab_term, tab_hype, tab_stress = st.tabs(["📊 TERMINAL", "🧪 HYPE FILTER", "🛡️ STRESS TEST"])

# --- TAB 1: TERMINAL ---
with tab_term:
    col_entry, col_chart = st.columns([1, 3])
    
    with col_entry:
        st.markdown("### 🔑 ASSET ENTRY")
        with st.container(border=True):
            t_in = st.text_input("Ticker", "HDFCBANK.NS").upper()
            s_in = st.number_input("Shares", min_value=0.0)
            p_in = st.number_input("Avg Price", min_value=0.0)
            if st.button("LOCK IN VAULT"):
                st.session_state.portfolio.append({"Ticker": t_in, "Shares": s_in, "Price": p_in})
                st.rerun()

    with col_chart:
        active = st.text_input("Search Market", "HDFCBANK.NS").upper()
        try:
            ticker = yf.Ticker(active, session=stealth_session)
            df = ticker.history(period="6mo")
            if not df.empty:
                # RSI
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rsi = 100 - (100 / (1 + (gain/loss))).iloc[-1]
                
                st.markdown(f"### ₹{df['Close'].iloc[-1]:,.2f} | <span class='gold-glow'>RSI: {rsi:.2f}</span>", unsafe_allow_html=True)
                
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                                                 increasing_line_color='#F9D342', decreasing_line_color='#FF4B4B')])
                fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=400, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
        except:
            st.error("Connection Throttled. Trying Stealth Protocol...")

# --- TAB 3: STRESS TEST & MONTE CARLO ---
with tab_stress:
    if st.session_state.portfolio:
        st.markdown("### 🌪️ Monte Carlo Odds Simulator")
        
        # Pulling Portfolio Data
        tickers = [x['Ticker'] for x in st.session_state.portfolio]
        data = yf.download(tickers, period="1y", session=stealth_session)['Close']
        
        # Calculate Returns & Volatility
        returns = data.pct_change().dropna()
        mu = returns.mean().mean() # Average daily return
        sigma = returns.std().mean() # Average volatility
        
        # Run Simulation
        sim_runs = 1000
        days = 30
        current_val = sum([x['Shares'] * x['Price'] for x in st.session_state.portfolio])
        
        final_results = []
        for _ in range(sim_runs):
            p = current_val
            for _ in range(days):
                p *= (1 + np.random.normal(mu, sigma))
            final_results.append(p)
            
        c1, c2 = st.columns([2, 1])
        with c1:
            fig_sim = go.Figure(data=[go.Histogram(x=final_results, marker_color='#F9D342', opacity=0.6)])
            fig_sim.update_layout(title="30-Day Wealth Probability Distribution", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_sim, use_container_width=True)
        
        with c2:
            st.markdown("<div class='vault-card'>", unsafe_allow_html=True)
            st.markdown("#### <span class='gold-glow'>THE VERDICT</span>", unsafe_allow_html=True)
            st.write(f"95% Confidence Floor: ₹{np.percentile(final_results, 5):,.2f}")
            st.write(f"Best Case (5% Top): ₹{np.percentile(final_results, 95):,.2f}")
            st.write(f"Avg Expected: ₹{np.mean(final_results):,.2f}")
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Add assets to the vault to unlock the simulator.")

# --- ASSET VAULT ---
st.write("---")
st.markdown("### 📊 THE VAULT ASSETS")
if st.session_state.portfolio:
    cols = st.columns(4)
    for i, s in enumerate(st.session_state.portfolio):
        with cols[i%4]:
            st.markdown(f"<div class='vault-card'><strong>{s['Ticker']}</strong><br><small>QTY: {s['Shares']}</small><br><span class='gold-glow'>₹{s['Price']}</span></div>", unsafe_allow_html=True)
