import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime

# 1. PAGE CONFIG
st.set_page_config(page_title="Nexus Invest | Decision Engine", page_icon="📡", layout="wide")

# --- 2. STYLING (The Nexus Dark Theme) ---
st.markdown("""
<style>
    .stApp { background-color: #0A0B10; color: #E0E0E0; }
    .nexus-card {
        background: rgba(255,255,255,0.03); border: 1px solid rgba(0,255,194,0.2);
        border-radius: 15px; padding: 20px; margin-bottom: 10px;
    }
    .mint-glow { color: #00FFC2; text-shadow: 0 0 10px rgba(0,255,194,0.3); }
</style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if "portfolio" not in st.session_state:
    st.session_state.portfolio = []

# --- 4. APP LAYOUT ---
tab1, tab2, tab3 = st.tabs(["📈 Terminal", "🧪 Hype Filter", "🛡️ Stress Tester"])

# --- TAB 1: TERMINAL (Restored Candlestick & Vault) ---
with tab1:
    col_side, col_chart = st.columns([1, 3])
    
    with col_side:
        st.markdown("### ➕ ADD ASSET")
        with st.container(border=True):
            t_input = st.text_input("Ticker", "TCS.NS").upper()
            s_input = st.number_input("Shares", min_value=0.0)
            p_input = st.number_input("Buy Price", min_value=0.0)
            if st.button("ADD TO VAULT"):
                st.session_state.portfolio.append({"Ticker": t_input, "Shares": s_input, "Buy Price": p_input})
                st.rerun()

    with col_chart:
        active_ticker = st.text_input("Search Market", "HDFCBANK.NS").upper()
        df = yf.Ticker(active_ticker).history(period="6mo")
        if not df.empty:
            # Stats
            curr_p = df['Close'].iloc[-1]
            # RSI Calculation
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi = 100 - (100 / (1 + (gain/loss))).iloc[-1]
            
            st.markdown(f"## ₹{curr_p:,.2f} | <span class='mint-glow'>RSI: {rsi:.2f}</span>", unsafe_allow_html=True)
            
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
            fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,b=0,t=0), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: HYPE FILTER (The New Feature) ---
with tab2:
    st.markdown("### 🧪 Hype vs. Health Filter")
    source_url = st.text_input("Paste YouTube Link or News URL")
    
    if source_url:
        col_analysis, col_meter = st.columns([2, 1])
        
        with col_analysis:
            st.info("Extracting insights...")
            # YouTube Transcript Extraction
            if "youtube.com" in source_url or "youtu.be" in source_url:
                try:
                    v_id = source_url.split("v=")[-1] if "v=" in source_url else source_url.split("/")[-1]
                    transcript_list = YouTubeTranscriptApi.get_transcript(v_id)
                    full_text = " ".join([t['text'] for t in transcript_list])
                    st.success("Transcript loaded! (Ready for Gemini analysis)")
                    with st.expander("View Transcript"):
                        st.write(full_text[:1000] + "...")
                except:
                    st.error("Could not fetch transcript. (Is it a private video?)")
            
        with col_meter:
            st.markdown("#### 🌡️ Hype Meter")
            # Logic: If RSI > 70 and Sentiment is High = Red Alert
            hype_val = 85 if rsi > 70 else 30 # Placeholder logic
            st.progress(hype_val/100)
            st.write(f"Status: {'⚠️ OVERBOUGHT HYPE' if hype_val > 70 else '✅ HEALTHY INTEREST'}")

# --- ASSET VAULT (Always visible at bottom) ---
st.write("---")
st.markdown("### 📊 ACTIVE ASSET VAULT")
if st.session_state.portfolio:
    cols = st.columns(4)
    for i, s in enumerate(st.session_state.portfolio):
        with cols[i%4]:
            st.markdown(f"<div class='nexus-card'><strong>{s['Ticker']}</strong><br>₹{s['Buy Price']} Avg</div>", unsafe_allow_html=True)
