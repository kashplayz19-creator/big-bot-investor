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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    .stApp { background-color: #FFFFFF; color: #202124; font-family: 'Inter', sans-serif; }
    .g-card { background: #FFFFFF; border: 1px solid #DADCE0; border-radius: 8px; padding: 16px; margin-bottom: 12px; }
    h1, h2, h3 { color: #202124 !important; font-weight: 600 !important; }
    .gain-pos { color: #188038; font-weight: 500; }
    .gain-neg { color: #D93025; font-weight: 500; }
    input { border: 1px solid #DADCE0 !important; border-radius: 4px !important; }
    .stTabs [data-baseweb="tab"] { font-weight: 600; color: #70757A; }
    .stTabs [aria-selected="true"] { color: #1A73E8 !important; border-bottom-color: #1A73E8 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. BACKEND & DATA ---
if "portfolio" not in st.session_state:
    st.session_state.portfolio = [
        {"Ticker": "HDFCBANK.NS", "Shares": 5, "Buy Price": 833.95},
        {"Ticker": "NIFTYBEES.NS", "Shares": 22, "Buy Price": 269.20},
    ]

try:
    creds_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    sheet = gspread.authorize(creds).open("My_Stock_Audits").sheet1 
except: st.sidebar.warning("Sheets not connected")

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model_pro = genai.GenerativeModel('gemini-1.5-pro')

# --- 4. BRANDING ---
st.title("📡 NEXUS INVEST")
st.markdown("##### Advanced Equity Intelligence Terminal")

# --- 5. TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["⚡ LIVE TERMINAL", "📊 YOUR PORTFOLIO", "🔍 AI AUDIT LOG", "🤖 STRATEGY CHAT"])

with tab1:
    col_a, col_b = st.columns([1, 2])
    with col_a:
        ticker_input = st.text_input("Enter NSE Ticker", value="HDFCBANK.NS").upper()
        @st.fragment(run_every=15)
        def show_price():
            try:
                p = yf.Ticker(ticker_input).fast_info['last_price']
                st.metric("Current Price", f"₹{p:.2f}")
                return p
            except: return 0
        current_price = show_price()
    with col_b:
        df = yf.download(ticker_input, period="1mo", interval="1d")
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
            fig.update_layout(template="plotly_white", height=350, margin=dict(l=0,r=0,b=0,t=0), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    # --- PORTFOLIO LOGIC ---
    total_market_val = 0
    total_day_gain = 0
    total_invested = 0
    portfolio_data = []

    for item in st.session_state.portfolio:
        t = yf.Ticker(item['Ticker'])
        h = t.history(period="2d")
        if not h.empty and len(h) >= 2:
            cur = h['Close'].iloc[-1]
            prev = h['Close'].iloc[-2]
            val = cur * item['Shares']
            dg = (cur - prev) * item['Shares']
            inv = item['Buy Price'] * item['Shares']
            
            total_market_val += val
            total_day_gain += dg
            total_invested += inv
            portfolio_data.append({**item, "cur": cur, "val": val, "dg": dg, "dgp": ((cur-prev)/prev)*100})

    # --- TOP HIGHLIGHTS CARD ---
    total_gain = total_market_val - total_invested
    tg_p = (total_gain / total_invested * 100) if total_invested > 0 else 0
    dg_p = (total_day_gain / (total_market_val - total_day_gain) * 100) if (total_market_val - total_day_gain) > 0 else 0

    st.markdown(f"""
    <div class="g-card" style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div style="background: #e6f4ea; padding: 15px; border-radius: 8px;">
            <small style="color: #188038;">DAY GAIN</small>
            <div style="font-size: 24px; font-weight: 600; color: #188038;">{'+' if total_day_gain >=0 else ''}₹{total_day_gain:,.2f}</div>
            <div style="color: #188038;">↑ {dg_p:.2f}%</div>
        </div>
        <div style="background: #fce8e6; padding: 15px; border-radius: 8px;">
            <small style="color: #d93025;">TOTAL GAIN</small>
            <div style="font-size: 24px; font-weight: 600; color: #d93025;">{'+' if total_gain >=0 else ''}₹{total_gain:,.2f}</div>
            <div style="color: #d93025;">↓ {abs(tg_p):.2f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.popover("➕ Add Investment"):
        nt = st.text_input("Ticker", "RELIANCE.NS").upper()
        ns = st.number_input("Shares", 1)
        np = st.number_input("Price", 100.0)
        if st.button("Confirm"):
            st.session_state.portfolio.append({"Ticker": nt, "Shares": ns, "Buy Price": np})
            st.rerun()

    # --- STOCK LIST ---
    for s in portfolio_data:
        tc = s['Ticker'].split('.')[0]
        d_map = {"HDFCBANK": "hdfcbank.com", "NIFTYBEES": "niftyindices.com"}
        l_url = f"https://logo.clearbit.com/{d_map.get(tc, tc.lower()+'.com')}"
        
        st.markdown(f"""
<div class="g-card" style="display: flex; align-items: center; justify-content: space-between;">
    <div style="display: flex; align-items: center; flex: 1;">
        <img src="{l_url}" width="40" height="40" style="border-radius: 4px; margin-right: 12px; border: 1px solid #f0f0f0;" onerror="this.onerror=null; this.src='https://ui-avatars.com/api/?name={tc}&background=f0f2f6&color=5f6368&bold=true';">
        <div>
            <div style="font-weight: 600;">{tc}</div>
            <div style="font-size: 12px; color: #70757A;">{s['Shares']} shares • ₹{s['Buy Price']:.2f} avg</div>
        </div>
    </div>
    <div style="text-align: center; flex: 1;">
        <div style="font-size: 14px; color: #70757A;">Price</div>
        <div style="font-weight: 500;">₹{s['cur']:,.2f}</div>
    </div>
    <div style="text-align: right; flex: 1;">
        <div style="font-weight: 600; font-size: 16px;">₹{s['val']:,.2f}</div>
        <div class="{'gain-pos' if s['dg'] >= 0 else 'gain-neg'}" style="font-size: 13px;">
            {'+' if s['dg'] >= 0 else ''}{s['dg']:,.2f} ({s['dgp']:+.2f}%)
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

with tab3:
    st.header("📋 Audit Stock Analysis")
    c1, c2 = st.columns(2)
    with c1:
        at = st.text_input("Audit Ticker", value=ticker_input)
        act = st.selectbox("Signal", ["BUY", "SELL", "WATCHLIST"])
    with c2:
        rsi = st.slider("RSI", 0, 100, 50)
        sup = st.number_input("Support", value=float(current_price)*0.95 if current_price else 0.0)
    if st.button("LOG AUDIT"):
        try:
            sheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), at, act, current_price, rsi, sup, "Logged from Nexus"])
            st.success("Logged!")
        except: st.error("Sheets Error")

with tab4:
    st.header("🤖 Strategy Chat")
    if "messages" not in st.session_state: st.session_state.messages = []
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    if p := st.chat_input("Ask Nexus..."):
        st.session_state.messages.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        with st.chat_message("assistant"):
            r = model_pro.generate_content(f"Market focus: {ticker_input}. {p}").text
            st.markdown(r)
            st.session_state.messages.append({"role": "assistant", "content": r})
