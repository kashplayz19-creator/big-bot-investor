import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# 1. PAGE CONFIG
st.set_page_config(page_title="Nexus Invest | Pro Terminal", page_icon="📡", layout="wide")

# --- 2. PREMIUM FINTECH UI ---
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
    .stTabs [aria-selected="true"] { border-bottom: 2px solid #00FFCC !important; }
    
    /* Fix for the 'Ghost Button' */
    div.stButton > button:first-child {
        background-color: #00FFCC !important;
        color: #0E1117 !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: none !important;
        height: 3em !important;
        width: 100% !important;
    }
    div.stButton > button:hover {
        background-color: #00d1a7 !important;
        box-shadow: 0px 0px 15px rgba(0, 255, 204, 0.4);
    }
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
    """, unsafe_allow_html=True)

# --- 3. BACKEND & PORTFOLIO DATA ---
# Update your shares and buy prices here!
PORTFOLIO_DATA = {
    "HDFCBANK.NS": {"shares": 3, "buy_price": 1388.00},
    "NIFTYBEES.NS": {"shares": 25, "buy_price": 235.90},
    "BEL.NS": {"shares": 5, "buy_price": 440.00}
}

try:
    creds_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    sheet = gspread.authorize(creds).open("My_Stock_Audits").sheet1 
except Exception as e:
    st.sidebar.error(f"Sheets Connection Error: {e}")

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model_pro = genai.GenerativeModel('gemini-1.5-pro')

# --- 4. BRANDING ---
st.markdown('<h1 class="nexus-title">📡 NEXUS INVEST</h1>', unsafe_allow_html=True)
st.markdown("### Advanced Equity Intelligence Terminal")

# --- 5. NAVIGATION TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["⚡ LIVE TERMINAL", "📊 YOUR PORTFOLIO", "🔍 AI AUDIT LOG", "🤖 STRATEGY CHAT"])

with tab1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    col_a, col_b = st.columns([1, 2])
    
    with col_a:
        ticker_input = st.text_input("Enter NSE Ticker", value="TATAMOTORS.NS").upper()
        
        @st.fragment(run_every=15)
        def show_price_card(ticker):
            try:
                data = yf.Ticker(ticker)
                price = data.fast_info.get('last_price') or data.history(period="1d")['Close'].iloc[-1]
                st.metric(label=f"Current Price", value=f"₹{price:.2f}")
                return price
            except:
                st.error("Ticker not found")
                return 0

        current_price = show_price_card(ticker_input)
    
    with col_b:
        chart_data = yf.download(ticker_input, period="1mo", interval="1d")
        if not chart_data.empty:
            if isinstance(chart_data.columns, pd.MultiIndex): 
                chart_data.columns = chart_data.columns.get_level_values(0)
            
            fig = go.Figure(data=[go.Candlestick(
                x=chart_data.index, open=chart_data['Open'], 
                high=chart_data['High'], low=chart_data['Low'], 
                close=chart_data['Close'], name="Price"
            )])
            
            # Interactive Layout with Scroll Zoom & Clean Dates
            fig.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis_rangeslider_visible=False, height=350,
                margin=dict(l=0,r=0,b=0,t=0),
                xaxis=dict(tickformat="%d %b", type="date", title="Date"),
                yaxis=dict(title="Price (₹)")
            )
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.header("📊 Portfolio Performance")
    
    p_cols = st.columns(len(PORTFOLIO_DATA))
    total_value = 0
    portfolio_rows = []

    # Clean, single-line loop to avoid the SyntaxError
    for i, (t, info) in enumerate(PORTFOLIO_DATA.items()):
        try:
            stock = yf.Ticker(t)
            curr = stock.fast_info.get('last_price') or stock.history(period="1d")['Close'].iloc[-1]
            val = curr * info['shares']
            total_value += val
            p_diff = ((curr - info['buy_price']) / info['buy_price']) * 100
            
            with p_cols[i]:
                st.metric(label=t.split('.')[0], value=f"₹{val:,.0f}", delta=f"{p_diff:.2f}%")
            
            portfolio_rows.append({"Ticker": t.split('.')[0], "Value": val})
        except Exception as e:
            st.warning(f"Could not load {t}")
            continue
# --- TAB 3: AI AUDIT LOG ---
with tab3:
    st.header("📋 Audit Stock Analysis")
    st.markdown("Use this to log your entry/exit logic to Google Sheets.")
    
    c1, c2 = st.columns(2)
    with c1:
        m_ticker = st.text_input("Audit Ticker", value=ticker_input)
        action = st.selectbox("Signal", ["BUY", "SELL", "WATCHLIST"])
    with c2:
        # We use the current_price from Tab 1 as a default
        rsi = st.slider("RSI Level (Strength)", 0, 100, 50)
        support = st.number_input("Support/Entry Level", value=float(current_price) * 0.95 if current_price else 0.0)
    
    notes = st.text_area("Audit Reasoning", placeholder="Why are we making this move?")
    
    if st.button("LOG AUDIT TO NEXUS DATABASE"):
        try:
            # Preparing the row for Google Sheets
            row = [
                datetime.now().strftime("%Y-%m-%d %H:%M"), 
                m_ticker, 
                action, 
                current_price, 
                rsi, 
                support, 
                notes
            ]
            sheet.append_row(row)
            st.success(f"Successfully logged {m_ticker} to My_Stock_Audits!")
            st.balloons()
        except Exception as e:
            st.error(f"Google Sheets Error: {e}")

# --- TAB 4: STRATEGY CHAT ---
with tab4:
    st.header("🤖 Nexus Invest Intelligence")
    st.info("AI Analysis specifically for the Indian Market (NSE/BSE).")

    # Chat UI Logic
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display past messages
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
    
    # User Input
    if prompt := st.chat_input("Ask Nexus Invest about a stock or strategy..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            # We give the AI 'Context' so it knows what stock you are currently looking at
            ai_context = f"""
            You are Nexus Invest Pro. The user is currently looking at {ticker_input} 
            trading at ₹{current_price:.2f}. 
            Answer their question using technical analysis principles: {prompt}
            """
            try:
                response = model_pro.generate_content(ai_context)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"AI Connection Error: {e}")
