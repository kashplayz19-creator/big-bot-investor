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

# --- 2. PREMIUM FINTECH UI (High-Contrast V2) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    .stApp { background-color: #FFFFFF; color: #202124; font-family: 'Inter', sans-serif; }
    
    /* Google Finance Card Style */
    .g-card {
        background: #FFFFFF;
        border: 1px solid #DADCE0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    
    /* Typography */
    h1, h2, h3 { color: #202124 !important; font-weight: 600 !important; }
    .metric-value { font-size: 24px; font-weight: 600; }
    .gain-pos { color: #188038; } /* Green */
    .gain-neg { color: #D93025; } /* Red */
    
    /* Clean Input Fields */
    input { border: 1px solid #DADCE0 !important; border-radius: 4px !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. BACKEND & PORTFOLIO DATA ---
if "portfolio" not in st.session_state:
    st.session_state.portfolio = [
        {"Ticker": "HDFCBANK.NS", "Shares": 5, "Buy Price": 833.95, "Date": "2026-03-12"},
        {"Ticker": "NIFTYBEES.NS", "Shares": 22, "Buy Price": 269.20, "Date": "2026-03-12"},
    ]

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
        ticker_input = st.text_input("Enter NSE Ticker", value="HDFCBANK.NS").upper()
        
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
    st.header("Portfolio")
    
    # --- ASSET BAR ---
    etf_count = sum([item['Shares'] for item in st.session_state.portfolio if "BEES" in item['Ticker']])
    stock_count = sum([item['Shares'] for item in st.session_state.portfolio if "BEES" not in item['Ticker']])
    total = etf_count + stock_count
    
    if total > 0:
        st.write(f"Asset Split: ETFs { (etf_count/total)*100:.1f}% | Stocks {(stock_count/total)*100:.1f}%")
        st.progress((etf_count/total))

    # --- SUMMARY CARD ---
    # (Calculated in loop below)
    
    # --- ADD INVESTMENT ---
    with st.popover("➕ Add Investment"):
        t_ticker = st.text_input("Ticker", "RELIANCE.NS").upper()
        col1, col2 = st.columns(2)
        t_shares = col1.number_input("Shares", 1)
        t_price = col2.number_input("Buy Price", 100.0)
        if st.button("Confirm"):
            st.session_state.portfolio.append({"Ticker": t_ticker, "Shares": t_shares, "Buy Price": t_price})
            st.rerun()

    # --- PORTFOLIO LIST ---
    for item in st.session_state.portfolio:
        stock = yf.Ticker(item['Ticker'])
        hist = stock.history(period="2d")
        current_p = hist['Close'].iloc[-1]
        prev_p = hist['Close'].iloc[-2]
        
        day_gain = (current_p - prev_p) * item['Shares']
        total_val = current_p * item['Shares']
        
        # Display as a clean row
        with st.container():
            st.markdown(f"""
            <div class="g-card" style="display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center;">
                    <img src="https://logo.clearbit.com/{item['Ticker'].split('.')[0].lower()}.com" width="40" style="border-radius: 50%; margin-right: 15px;">
                    <div>
                        <strong>{item['Ticker'].split('.')[0]}</strong><br>
                        <small style="color: #70757A;">Qty: {item['Shares']} | Avg: ₹{item['Buy Price']:.2f}</small>
                    </div>
                </div>
                <div style="text-align: right;">
                    <strong>₹{current_val:,.2f}</strong><br>
                    <span class="{'gain-pos' if day_gain >= 0 else 'gain-neg'}">
                        {'+' if day_gain >=0 else ''}{day_gain:,.2f} ({((current_p-prev_p)/prev_p)*100:.2f}%)
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
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
    st.header("🤖 Nexus Strategy Intelligence")
    
    col_chat, col_news = st.columns([2, 1])
    
    with col_chat:
        if "messages" not in st.session_state: st.session_state.messages = []
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        
        if prompt := st.chat_input("Analyze market sentiment..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                ai_context = f"You are Nexus Invest. Current focus: {ticker_input} at ₹{current_price}. Analyze this: {prompt}"
                response = model_pro.generate_content(ai_context)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})

    with col_news:
        st.subheader("📰 Market Radar")
        try:
            news_stock = yf.Ticker(ticker_input)
            news_items = news_stock.news[:5] # Get top 5 news stories
            
            for article in news_items:
                st.markdown(f"""
                **{article['title']}** *Source: {article['publisher']}* [Read More]({article['link']})
                ---
                """)
        except:
            st.write("No recent news found for this ticker.")
