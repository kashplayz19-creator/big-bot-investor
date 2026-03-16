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
    st.header("📊 Nexus Portfolio Manager")
    
    # 1. ADD NEW TRANSACTION (The Input Section)
    with st.expander("➕ Add New Transaction", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        with col1: t_ticker = st.text_input("Ticker", value="TATAMOTORS.NS").upper()
        with col2: t_shares = st.number_input("Shares", min_value=1, value=1)
        with col3: t_price = st.number_input("Buy Price (₹)", min_value=0.1, value=100.0)
        with col4: t_date = st.date_input("Purchase Date")
        
        if st.button("Add to Portfolio"):
            st.session_state.portfolio.append({
                "Ticker": t_ticker, "Shares": t_shares, 
                "Buy Price": t_price, "Date": str(t_date)
            })
            st.success(f"Added {t_ticker}!")

    # 2. PORTFOLIO CALCULATION
    if st.session_state.portfolio:
        display_data = []
        total_investment = 0
        total_current_value = 0

        for item in st.session_state.portfolio:
            stock = yf.Ticker(item['Ticker'])
            # Get live price
            current_p = stock.fast_info.get('last_price') or stock.history(period="1d")['Close'].iloc[-1]
            
            invested = item['Shares'] * item['Buy Price']
            current_val = item['Shares'] * current_p
            pl_rupees = current_val - invested
            pl_percent = (pl_rupees / invested) * 100
            
            total_investment += invested
            total_current_value += current_val
            
            display_data.append({
                "Ticker": item['Ticker'].split('.')[0],
                "Shares": item['Shares'],
                "Buy Price": f"₹{item['Buy Price']:.2f}",
                "Current": f"₹{current_p:.2f}",
                "P&L (%)": f"{pl_percent:+.2f}%",
                "Value": current_val
            })

        # Summary Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Investment", f"₹{total_investment:,.2f}")
        m2.metric("Current Value", f"₹{total_current_value:,.2f}", delta=f"{((total_current_value-total_investment)/total_investment)*100:.2f}%")
        m3.metric("Total P&L", f"₹{total_current_value - total_investment:,.2f}")

        # Unique Google Finance Style Table
        df_portfolio = pd.DataFrame(display_data)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.table(df_portfolio) 
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Donut Chart for Diversification
        fig_donut = px.pie(df_portfolio, values='Value', names='Ticker', hole=0.6,
                           color_discrete_sequence=px.colors.sequential.Mint_r)
        fig_donut.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=350)
        st.plotly_chart(fig_donut, use_container_width=True)
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
