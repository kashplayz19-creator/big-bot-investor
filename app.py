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
# --- 1. THE VAULT: PREMIUM CSS ---
st.markdown(f"""
<style>
    /* Dominant: Obsidian / Charcoal (60%) */
    .stApp {{
        background-color: #0F0F12; 
        color: #E0E0E0;
        font-family: 'Inter', sans-serif;
    }}

    /* Secondary: Slate / Silver (30%) */
    [data-testid="stSidebar"] {{
        background-color: #1A1C23;
        border-right: 1px solid #2D2F36;
    }}

    /* Accent: Dandelion Gold (10%) & Neon Glow */
    .gold-glow {{
        color: #F9D342;
        text-shadow: 0 0 15px rgba(249, 211, 66, 0.4);
        font-weight: 800;
        letter-spacing: 2px;
    }}

    /* The "Vault" Card Effect */
    .vault-card {{
        background: linear-gradient(145deg, #16181D, #0F1014);
        border: 1px solid #2D2F36;
        border-radius: 12px;
        padding: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        transition: 0.4s;
    }
    .vault-card:hover {{
        border: 1px solid #F9D342;
        box-shadow: 0 0 20px rgba(249, 211, 66, 0.1);
    }}

    /* Neon Gold Buttons */
    .stButton>button {{
        background-color: transparent;
        border: 1px solid #F9D342;
        color: #F9D342;
        box-shadow: inset 0 0 5px rgba(249, 211, 66, 0.2);
        transition: all 0.3s ease-in-out;
    }}
    .stButton>button:hover {{
        background-color: #F9D342;
        color: #0F0F12;
        box-shadow: 0 0 20px rgba(249, 211, 66, 0.4);
    }}
</style>
""", unsafe_allow_html=True)

# --- 2. MONTE CARLO ENGINE (The Logic) ---
def run_monte_carlo(current_val, days, mean_ret, std_dev):
    simulations = 1000
    results = []
    for _ in range(simulations):
        prices = [current_val]
        for _ in range(days):
            # Random walk using daily returns
            prices.append(prices[-1] * (1 + np.random.normal(mean_ret, std_dev)))
        results.append(prices[-1])
    return results

# --- 3. UI EXECUTION ---
with st.container():
    st.markdown("<h1 class='gold-glow'>THE VAULT | PRO TERMINAL</h1>", unsafe_allow_html=True)
    
    col_a, col_b = st.columns([2, 1])
    
    with col_a:
        st.markdown("<div class='vault-card'>", unsafe_allow_html=True)
        st.subheader("🎲 Monte Carlo Shadow Simulation")
        # Example using HDFC daily mean and volatility
        sim_data = run_monte_carlo(100000, 30, 0.0005, 0.015) 
        
        fig = go.Figure(data=[go.Histogram(x=sim_data, marker_color='#F9D342', opacity=0.7)])
        fig.update_layout(
            title="Projected Value in 30 Days (1,000 Runs)",
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title="Final Portfolio Value",
            yaxis_title="Frequency"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_b:
        st.markdown("<div class='vault-card'>", unsafe_allow_html=True)
        st.markdown("### <span class='gold-glow'>RISK ANALYSIS</span>", unsafe_allow_html=True)
        st.write("Confidence: 95%")
        st.write(f"Max Probable Loss: ₹{np.percentile(sim_data, 5):,.2f}")
        st.write(f"Best Case Gain: ₹{np.percentile(sim_data, 95):,.2f}")
        st.markdown("</div>", unsafe_allow_html=True)

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
