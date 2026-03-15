import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

# 1. PAGE CONFIG
st.set_page_config(
    page_title="Big Bot Investor | AI Stock Auditor", 
    page_icon="📈", 
    layout="wide"
)

# --- 2. GOOGLE SHEETS SETUP ---
try:
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open("My_Stock_Audits").sheet1 
except Exception as e:
    st.sidebar.error(f"Google Sheets Connection Error: {e}")

# --- 3. IDENTITY & SECURITY SETUP ---
SYSTEM_BEHAVIOR = """
You are 'Big Bot Pro', a specialized AI for the Indian Stock Market.
Your expertise includes Technical Analysis (RSI, Moving Averages) and Fundamental Analysis.
Tone: Professional and concise. Use Indian formatting (Lakhs/Crores).
"""

if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

if not api_key:
    st.warning("Please add your API Key to begin.")
    st.stop()

genai.configure(api_key=api_key)
model_flash = genai.GenerativeModel('gemini-1.5-flash')
model_pro = genai.GenerativeModel(model_name='gemini-1.5-pro', system_instruction=SYSTEM_BEHAVIOR)

# --- 4. HELPER FUNCTIONS ---
def log_audit_to_sheet(ticker, audit_text):
    try:
        row = [datetime.now().strftime("%Y-%m-%d %H:%M"), ticker.upper(), audit_text[:500]]
        sheet.append_row(row)
    except:
        pass

# --- 5. MAIN UI ---
st.title("🚀 MISSION: BIG BOT")
st.markdown("### AI-Powered Equity Auditor for the Indian Market")

# --- LIVE PRICE SECTION (Auto-refreshes) ---
st.header("📈 Live Market Watch")

@st.fragment(run_every=15)
# --- LIVE PRICE SECTION (With Retry Logic) ---
st.header("📈 Live Market Watch")

@st.fragment(run_every=15)
def show_live_price():
    t_input = st.text_input("Enter Ticker (e.g. TATAMOTORS.NS, NIFTYBEES.NS)", value="TATAMOTORS.NS").upper()
    if t_input:
        try:
            stock_data = yf.Ticker(t_input)
            # Strategy 1: Try the fast info first
            live_p = stock_data.fast_info['last_price']
            
            # Strategy 2: If fast_info returns 0 or None (common for some Indian stocks), use history
            if live_p is None or live_p == 0:
                hist = stock_data.history(period="1d")
                if not hist.empty:
                    live_p = hist['Close'].iloc[-1]
            
            curr = stock_data.fast_info.get('currency', 'INR')
            
            if live_p and live_p > 0:
                st.metric(label=f"Live Price: {t_input}", value=f"{curr} {live_p:.2f}")
                return t_input, live_p
            else:
                st.warning(f"Data for {t_input} is currently flat or unavailable. Market might be closed.")
                
        except Exception as e:
            st.error(f"Ticker {t_input} not found. Try adding .NS (NSE) or .BO (BSE).")
    return None, None

# This line MUST stay outside the function to actually run it
active_ticker, active_price = show_live_price()

# --- MANUAL AUDIT FORM ---
st.divider()
st.header("📊 Manual Stock Entry")
col1, col2 = st.columns(2)

with col1:
    m_ticker = st.text_input("Stock Name", value=active_ticker if active_ticker else "")
    action = st.selectbox("Action", ["BUY", "SELL", "WATCHLIST"])
    m_price = st.number_input("Price to Log", value=active_price if active_price else 0.0)

with col2:
    rsi_val = st.number_input("RSI (14-day)", min_value=0, max_value=100)
    support = st.number_input("Support Level", min_value=0.0)

notes = st.text_area("Analysis Notes")

if st.button("📝 Save Entry to Sheets"):
    date_str = datetime.now().strftime("%Y-%m-%d")
    row_to_add = [date_str, m_ticker.upper(), action, m_price, rsi_val, support, notes]
    try:
        sheet.append_row(row_to_add)
        st.success(f"Saved {m_ticker} to My_Stock_Audits!")
    except Exception as e:
        st.error(f"Error: {e}")

# --- CHARTING SECTION ---
st.divider()
st.subheader("📉 Technical Charts")
chart_ticker = st.selectbox("Select Chart", ["HDFCBANK.NS", "SBIN.NS", "TCS.NS", "BEL.NS", "TATAMOTORS.NS"])
chart_data = yf.download(chart_ticker, period="1mo", interval="1d")

if not chart_data.empty:
    # Flatten columns if multi-indexed
    if isinstance(chart_data.columns, pd.MultiIndex):
        chart_data.columns = chart_data.columns.get_level_values(0)
        
    fig = go.Figure(data=[go.Candlestick(
        x=chart_data.index,
        open=chart_data['Open'],
        high=chart_data['High'],
        low=chart_data['Low'],
        close=chart_data['Close']
    )])
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=400)
    st.plotly_chart(fig, use_container_width=True)

# --- AI CHAT SECTION ---
st.divider()
st.subheader("🤖 Chat with Big Bot Pro")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask Big Bot Pro..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = model_pro.generate_content(prompt)
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
