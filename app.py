import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime

# 1. PAGE CONFIG & THEME
st.set_page_config(page_title="Nexus Invest | Pro", page_icon="📡", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0A0B10; color: #E0E0E0; }
    .nexus-card {
        background: rgba(255,255,255,0.03); border: 1px solid rgba(0,255,194,0.2);
        border-radius: 15px; padding: 20px; margin-bottom: 15px;
    }
    .mint-glow { color: #00FFC2; text-shadow: 0 0 10px rgba(0,255,194,0.3); }
</style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR: SECRETS & INPUTS ---
with st.sidebar:
    st.markdown("### 🔑 API CONFIG")
    gemini_key = st.text_input("Enter Gemini API Key", type="password")
    if gemini_key:
        genai.configure(api_key=gemini_key)
    
    st.write("---")
    st.markdown("### ➕ ASSET MANAGER")
    with st.form("add_asset"):
        t_in = st.text_input("Ticker", "HDFCBANK.NS").upper()
        s_in = st.number_input("Shares", min_value=0.0)
        p_in = st.number_input("Price", min_value=0.0)
        if st.form_submit_button("ADD TO VAULT"):
            if "portfolio" not in st.session_state: st.session_state.portfolio = []
            st.session_state.portfolio.append({"Ticker": t_in, "Shares": s_in, "Price": p_in})
            st.rerun()

# --- 3. MAIN INTERFACE ---
tab_terminal, tab_hype, tab_stress = st.tabs(["📈 TERMINAL", "🧪 HYPE FILTER", "🛡️ STRESS TEST"])

# --- TAB 1: TERMINAL (CANDLESTICKS) ---
with tab_terminal:
    active_ticker = st.text_input("Search Market", "HDFCBANK.NS").upper()
    df = yf.Ticker(active_ticker).history(period="6mo")
    
    if not df.empty:
        # RSI Logic
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain/loss))).iloc[-1]
        
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"## {active_ticker} | <span class='mint-glow'>₹{df['Close'].iloc[-1]:,.2f}</span>", unsafe_allow_html=True)
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
            fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0,r=0,b=0,t=0), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("#### Market Health")
            st.metric("RSI (14)", f"{rsi:.2f}", delta="Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral")
            st.progress(rsi/100)

# --- TAB 2: HYPE FILTER (GEMINI INTEGRATION) ---
with tab_hype:
    st.markdown("### 🧪 Hype vs. Health Analyzer")
    yt_url = st.text_input("Paste YouTube URL for Sentiment Analysis")
    
    if yt_url and gemini_key:
        try:
            # 1. Get Transcript
            v_id = yt_url.split("v=")[-1] if "v=" in yt_url else yt_url.split("/")[-1]
            transcript = YouTubeTranscriptApi.get_transcript(v_id)
            text = " ".join([t['text'] for t in transcript])
            
            # 2. Gemini Analysis
            model = genai.GenerativeModel('gemini-pro')
            prompt = f"""
            Analyze this stock tip transcript: '{text[:4000]}'
            The stock currently has an RSI of {rsi:.2f}.
            Provide:
            1. Sentiment (Bullish/Bearish/Neutral)
            2. Hype Score (0-100)
            3. Credibility Warning: Does the speaker provide data or just 'trust me' vibes?
            """
            response = model.generate_content(prompt)
            
            col_res, col_meter = st.columns([2, 1])
            with col_res:
                st.markdown("<div class='nexus-card'>", unsafe_allow_html=True)
                st.markdown(f"#### 🤖 Gemini Analysis for {active_ticker}")
                st.write(response.text)
                st.markdown("</div>", unsafe_allow_html=True)
            with col_meter:
                st.markdown("#### 🌡️ Hype Meter")
                # Simple logic for meter color
                st.warning("⚠️ High Hype detected" if "hype" in response.text.lower() else "✅ Normal Discussion")
        except Exception as e:
            st.error(f"Analysis failed: {e}")
    elif not gemini_key:
        st.warning("Please enter your Gemini API Key in the sidebar to use the Hype Filter.")

# --- FOOTER VAULT ---
st.write("---")
st.markdown("### 📊 ACTIVE ASSET VAULT")
if "portfolio" in st.session_state and st.session_state.portfolio:
    p_cols = st.columns(4)
    for i, s in enumerate(st.session_state.portfolio):
        with p_cols[i%4]:
            st.markdown(f"<div class='nexus-card'><strong>{s['Ticker']}</strong><br>₹{s['Price']} Avg</div>", unsafe_allow_html=True)
