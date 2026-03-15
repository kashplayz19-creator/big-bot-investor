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
# --- CUSTOM STYLING ---
st.markdown("""
    <style>
    /* Card-like styling for metrics */
    [data-testid="stMetricValue"] {
        font-size: 30px;
        color: #00ffcc;
    }
    div.stButton > button:first-child {
        background-color: #00ffcc;
        color: black;
        border-radius: 20px;
        border: none;
        width: 100%;
    }
    .main {
        background-color: #0e1117;
    }
    </style>
    """, unsafe_allow_html=True)

# --- NAVIGATION TABS ---
tab1, tab2, tab3 = st.tabs(["📈 Market Live", "📊 Audit Entry", "🤖 AI Strategy"])

with tab1:
    # Move your Live Price section and Charts here
    pass

with tab2:
    # Move your Manual Entry form here
    pass

with tab3:
    # Move the Chat section here
    pass
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

st.divider()

# --- LIVE PRICE SECTION ---
st.header("📈 Live Market Watch")

@st.fragment(run_every=15)
def show_live_price():
    t_input = st.text_input("Enter Ticker (e.g. TATAMOTORS.NS)", value="TATAMOTORS.NS").upper()
    if t_input:
        try:
            stock_data = yf.Ticker(t_input)
            live_p = stock_data.fast_info['last_price']
            
            # Sunday Backup: if market closed, get last Friday's close
            if live_p is None or live_p == 0:
                hist = stock_data.history(period="1d")
                if not hist.empty:
                    live_p = hist['Close'].iloc[-1]
            
            curr = stock_data.fast_info.get('currency', 'INR')
            st.metric(label=f"Price: {t_input}", value=f"{curr} {live_p:.2f}")
            return t_input, live_p
        except Exception as e:
            st.error(f"Error fetching {t_input}: {e}")
    return None, None

# Call the function
active_ticker, active_price = show_live_price()

st.divider()

# --- MANUAL AUDIT FORM ---
st.header("📊 Manual Stock Entry")
col1, col2 = st.columns(2)

with col1:
    # All these are now correctly indented!
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
        st.error(f"Error saving: {e}")

# --- CHARTING SECTION ---
st.divider()
st.subheader("📉 Technical Charts")
chart_ticker = st.selectbox("Select Chart", ["HDFCBANK.NS", "SBIN.NS", "TCS.NS", "BEL.NS", "TATAMOTORS.NS"])
chart_data = yf.download(chart_ticker, period="1mo", interval="1d")

if not chart_data.empty:
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
