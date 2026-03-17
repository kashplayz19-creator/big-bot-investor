import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import google.generativeai as genai
from curl_cffi import requests
from youtube_transcript_api import YouTubeTranscriptApi

# --- 1. THE STEALTH ENGINE ---
# We create a session that mimics a real Chrome browser to bypass Yahoo's blocks.
stealth_session = requests.Session(impersonate="chrome124")

st.set_page_config(page_title="Nexus Invest | Ultra", page_icon="🛡️", layout="wide")

# CSS Styling
st.markdown("""
<style>
    .stApp { background-color: #0A0B10; color: #E0E0E0; }
    .nexus-card {
        background: rgba(0, 255, 194, 0.05); border: 1px solid rgba(0, 255, 194, 0.2);
        border-radius: 12px; padding: 20px; margin-bottom: 15px;
    }
    .mint { color: #00FFC2; }
    .danger { color: #FF4B4B; }
</style>
""", unsafe_allow_html=True)

# --- 2. SHARED DATA LOGIC ---
if "portfolio" not in st.session_state:
    st.session_state.portfolio = []

# --- 3. APP TABS ---
tab_terminal, tab_hype, tab_stress = st.tabs(["📈 TERMINAL", "🧪 HYPE FILTER", "🛡️ STRESS TESTER"])

# --- TAB 1: TERMINAL (With Stealth Mode) ---
with tab_terminal:
    active_ticker = st.text_input("Enter Ticker (e.g., TCS.NS, HDFCBANK.NS)", "HDFCBANK.NS").upper()
    
    try:
        # Pass the stealth session to yfinance
        ticker_data = yf.Ticker(active_ticker, session=stealth_session)
        df = ticker_data.history(period="6mo")
        
        if not df.empty:
            # Quick RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi = 100 - (100 / (1 + (gain/loss))).iloc[-1]
            
            st.markdown(f"## {active_ticker} | <span class='mint'>₹{df['Close'].iloc[-1]:,.2f}</span>", unsafe_allow_html=True)
            st.metric("RSI (14)", f"{rsi:.2f}", "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral")
            
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
            fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,b=0,t=0), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Stealth connection failed. Yahoo might be heavily throttled: {e}")

# --- TAB 3: STRESS TESTER (New Logic) ---
with tab_stress:
    st.markdown("### 🌪️ Portfolio Stress Simulation")
    
    if not st.session_state.portfolio:
        st.warning("Add assets to your vault in the sidebar first!")
    else:
        # Fetching data for all assets in vault to check correlation
        tickers = [item['Ticker'] for item in st.session_state.portfolio]
        
        with st.spinner("Calculating risk matrices..."):
            try:
                # Download combined data
                data = yf.download(tickers, period="1y", session=stealth_session)['Close']
                returns = data.pct_change().dropna()
                corr_matrix = returns.corr()
                
                # Visual: Correlation Heatmap
                st.markdown("#### 🤝 Asset Correlation")
                st.write("Do your assets move together? (1.0 = Same, 0 = Different)")
                st.dataframe(corr_matrix.style.background_gradient(cmap='RdYlGn'))
                
                # Crash Scenarios
                st.markdown("---")
                st.markdown("#### 🚨 Crash Simulations (2026 Fed Baseline)")
                
                total_value = sum([i['Shares'] * i['Price'] for i in st.session_state.portfolio])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.error("Scenario: Severely Adverse (-50%)")
                    st.write(f"Estimated Loss: ₹{total_value * 0.5:,.2f}")
                    st.caption("Based on 2026 Fed Stress Test equity shock.")
                
                with col2:
                    st.warning("Scenario: Tech Melt (-20%)")
                    # Simplified logic: apply more weight to tech tickers if they exist
                    st.write(f"Estimated Loss: ₹{total_value * 0.2:,.2f}")
                
            except Exception as e:
                st.error("Could not run stress test. Ensure all tickers in your vault are valid.")

# --- SIDEBAR (Persistent Vault) ---
with st.sidebar:
    st.markdown("### 🔑 API & VAULT")
    gemini_key = st.text_input("Gemini Key", type="password")
    if gemini_key: genai.configure(api_key=gemini_key)
    
    with st.form("vault_form"):
        t = st.text_input("Ticker").upper()
        s = st.number_input("Shares", min_value=0.1)
        p = st.number_input("Avg Price", min_value=0.1)
        if st.form_submit_button("ADD TO VAULT"):
            st.session_state.portfolio.append({"Ticker": t, "Shares": s, "Price": p})
            st.rerun()
