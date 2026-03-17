import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. PAGE CONFIG
st.set_page_config(page_title="Nexus Invest | Decision Engine", page_icon="📡", layout="wide")

# --- 2. THE ULTIMATE "CARBON MINT" CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@500&display=swap');
    .stApp { background-color: #0A0B10; color: #E0E0E0; font-family: 'Inter', sans-serif; }
    
    /* GLASSMORPHISM CARD */
    .nexus-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.01) 100%);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 15px;
        padding: 20px;
        backdrop-filter: blur(12px);
        margin-bottom: 15px;
        transition: 0.3s;
    }
    .nexus-card:hover { border: 1px solid #00FFC2; transform: translateY(-3px); }

    /* TICKER TAPE */
    @keyframes scroll { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .ticker-wrap {
        position: fixed; bottom: 0; left: 0; width: 100%; overflow: hidden;
        background: rgba(0, 255, 194, 0.05); border-top: 1px solid rgba(0, 255, 194, 0.2);
        height: 35px; z-index: 999; display: flex; align-items: center;
    }
    .ticker-item { display: inline-block; padding: 0 40px; color: #00FFC2; font-family: 'JetBrains Mono', monospace; font-size: 12px; animation: scroll 25s linear infinite; }

    .mint-glow { color: #00FFC2; text-shadow: 0 0 10px rgba(0,255,194,0.3); font-weight: 800; }
    .big-stat { font-family: 'JetBrains Mono', monospace; font-size: 32px !important; font-weight: 800; }
    
    /* STYLE BUTTONS TO LOOK LIKE GOOGLE FINANCE BUT MINT */
    .stButton>button {
        background-color: transparent; border: 1px solid #00FFC2; color: #00FFC2;
        border-radius: 8px; transition: 0.3s; width: 100%;
    }
    .stButton>button:hover { background-color: rgba(0, 255, 194, 0.1); border: 1px solid #00FFC2; color: #00FFC2; }
</style>
""", unsafe_allow_html=True)

# --- 3. DATABASE (SESSION STATE) ---
if "portfolio" not in st.session_state:
    st.session_state.portfolio = [] # Start empty or with your HDFC/NiftyBEES data

# --- 4. MODULAR GRID ---
col_sidebar, col_main = st.columns([1, 3])

# --- SIDEBAR: COMMAND CENTER (ADD ASSETS HERE) ---
with col_sidebar:
    st.markdown("### 🛠️ COMMAND CENTER")
    
    with st.container(border=True):
        st.markdown("##### ➕ ADD INVESTMENT")
        new_ticker = st.text_input("Ticker (e.g. BEL.NS)", "").upper()
        new_shares = st.number_input("Shares", min_value=0.0, step=1.0)
        new_price = st.number_input("Buy Price (₹)", min_value=0.0)
        
        if st.button("EXECUTE ADD"):
            if new_ticker:
                st.session_state.portfolio.append({
                    "Ticker": new_ticker, "Shares": new_shares, "Buy Price": new_price
                })
                st.success(f"Added {new_ticker}")
                st.rerun()

    st.markdown("##### 📝 HYPE FILTER (Coming Soon)")
    st.caption("Paste a news link below to analyze sentiment vs RSI.")
    st.text_input("URL Link", placeholder="YouTube or News URL", disabled=True)

# --- MAIN ENGINE ---
with col_main:
    # Google Finance Style Header
    st.markdown("<h1 style='letter-spacing: 5px;'>NEXUS <span class='mint-glow'>INVEST</span></h1>", unsafe_allow_html=True)
    
    active_ticker = st.text_input("🔍 SEARCH UNIVERSAL MARKET", value="HDFCBANK.NS").upper()
    
    # FETCH DATA
    try:
        t_obj = yf.Ticker(active_ticker)
        # 1-Year data for better context
        df = t_obj.history(period="6mo")
        
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            curr_p = df['Close'].iloc[-1]
            prev_p = df['Close'].iloc[-2]
            delta = curr_p - prev_p
            
            # BIG STATS BOX
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f"<small>CURRENT PRICE</small><br><span class='big-stat'>₹{curr_p:,.2f}</span>", unsafe_allow_html=True)
            with c2: st.markdown(f"<small>DAY CHANGE</small><br><span style='color:{'#00FFC2' if delta >=0 else '#FF4B4B'}'>{'▲' if delta >=0 else '▼'} {abs(delta):.2f}</span>", unsafe_allow_html=True)
            with c3:
                # RSI CALCULATION FOR HYPE FILTER
                delta_p = df['Close'].diff()
                gain = (delta_p.where(delta_p > 0, 0)).rolling(window=14).mean()
                loss = (-delta_p.where(delta_p < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs)).iloc[-1]
                st.markdown(f"<small>RSI (HEALTH)</small><br><span>{rsi:.2f}</span>", unsafe_allow_html=True)

            # PROFESSIONAL CANDLESTICK CHART
            fig = go.Figure(data=[go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                increasing_line_color='#00FFC2', decreasing_line_color='#FF4B4B'
            )])
            fig.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                height=450, margin=dict(l=0,r=0,b=0,t=0), xaxis_rangeslider_visible=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Invalid Ticker.")
    except:
        st.error("Connection Error.")

# --- BOTTOM VAULT: ACTIVE ASSET VAULT ---
st.write("---")
st.markdown("### 📊 ACTIVE ASSET VAULT")
if st.session_state.portfolio:
    v_cols = st.columns(4) # Grid of 4
    for i, s in enumerate(st.session_state.portfolio):
        with v_cols[i % 4]:
            st.markdown(f"""
            <div class='nexus-card'>
                <strong>{s['Ticker']}</strong><br>
                <small>{s['Shares']} Shares</small><br>
                <span class='mint-glow'>Avg: ₹{s['Buy Price']}</span>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("No investments added yet. Use the Command Center on the left to add your first stock!")

# --- TICKER TAPE ---
st.markdown("""<div class="ticker-wrap"><div class="ticker-item">HDFCBANK: ₹... | NIFTY 50: ₹... | RELIANCE: ₹... | NEXUS STATUS: ONLINE</div></div>""", unsafe_allow_html=True)
