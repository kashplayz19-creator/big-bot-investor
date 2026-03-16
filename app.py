import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# 1. PAGE CONFIG
st.set_page_config(
    page_title="Nexus Invest | Pro Terminal", 
    page_icon="📡", # Swapped to a satellite/nexus icon
    layout="wide"
)

# --- 2. PREMIUM FINTECH UI (From AI Studio) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    [data-testid="stMetricValue"] { font-size: 28px; color: #00FFCC !important; }
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap; background-color: transparent;
        border-radius: 4px 4px 0px 0px; color: white;
    }
    .stTabs [aria-selected="true"] { border-bottom: 2px solid #00FFCC !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BACKEND SETUP (API & SHEETS) ---
try:
    creds_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    sheet = gspread.authorize(creds).open("My_Stock_Audits").sheet1 
except Exception as e:
    st.sidebar.error(f"Sheets Connection Error: {e}")

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model_pro = genai.GenerativeModel('gemini-1.5-pro')

# --- 4. BRANDING & NAVIGATION ---
st.markdown("""
    <style>
    .nexus-title {
        font-size: 50px;
        font-weight: 800;
        background: linear-gradient(45deg, #00FFCC, #0099FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: 2px;
        margin-bottom: -10px;
    }
    </style>
    <h1 class="nexus-title">📡 NEXUS INVEST</h1>
    """, unsafe_allow_html=True)
st.markdown("### Advanced Equity Intelligence Terminal")

tab1, tab2, tab3 = st.tabs(["⚡ LIVE TERMINAL", "🔍 AI AUDIT LOG", "🤖 STRATEGY CHAT"])

with tab1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    col_a, col_b = st.columns([1, 2])
    
    with col_a:
        ticker_input = st.text_input("Enter NSE Ticker", value="TATAMOTORS.NS").upper()
        
        @st.fragment(run_every=15)
        def show_price_card(ticker):
            # ... (rest of function code)
            try:
                data = yf.Ticker(ticker)
                # Strategy 1: Fast Info
                price = data.fast_info.get('last_price')
                
                # Strategy 2: If Strategy 1 fails, try regular info
                if price is None or price == 0:
                    price = data.info.get('regularMarketPrice')
                
                # Strategy 3: If still nothing, grab the very last 1-minute candle
                if price is None or price == 0:
                    hist = data.history(period="1d", interval="1m")
                    if not hist.empty:
                        price = hist['Close'].iloc[-1]
                
                if price and price > 0:
                    st.metric(label=f"Current Price", value=f"₹{price:.2f}")
                    return price
                else:
                    st.error(f"Waiting for {ticker} data...")
                    return 0
            except Exception as e:
                st.error(f"Connection Error: {e}")
                return 0

        current_price = show_price_card(ticker_input)
    
    with col_b:
        # DARK MODE CHARTING (From AI Studio)
        chart_data = yf.download(ticker_input, period="1mo", interval="1d")
        if not chart_data.empty:
            if isinstance(chart_data.columns, pd.MultiIndex):
                chart_data.columns = chart_data.columns.get_level_values(0)
            fig = go.Figure(data=[go.Candlestick(x=chart_data.index, open=chart_data['Open'], high=chart_data['High'], low=chart_data['Low'], close=chart_data['Close'])])
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_rangeslider_visible=False, height=300, margin=dict(l=0,r=0,b=0,t=0))
            st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.header("📋 Audit Stock Analysis")
    c1, c2 = st.columns(2)
    with c1:
        m_ticker = st.text_input("Audit Ticker", value=ticker_input)
        action = st.selectbox("Signal", ["BUY", "SELL", "WATCHLIST"])
    with c2:
        rsi = st.slider("RSI Level", 0, 100, 50)
        support = st.number_input("Support Level", value=current_price * 0.95 if current_price else 0.0)
    
    notes = st.text_area("Audit Reasoning")
    if st.button("LOG AUDIT TO SHEETS"):
        try:
            row = [datetime.now().strftime("%Y-%m-%d"), m_ticker, action, current_price, rsi, support, notes]
            sheet.append_row(row)
            st.success("Audit Logged!")
        except Exception as e:
            st.error(f"Failed: {e}")

with tab3:
    st.header("🤖 Nexus Invest Intelligence") # <--- Indent this!
    if "messages" not in st.session_state: 
        st.session_state.messages = []
    
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): 
            st.markdown(m["content"])
    
    if prompt := st.chat_input("Ask about market trends..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): 
            st.markdown(prompt)
        with st.chat_message("assistant"):
            response = model_pro.generate_content(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
