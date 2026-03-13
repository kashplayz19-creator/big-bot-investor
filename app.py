import streamlit as st
import yfinance as yf
import google.generativeai as genai
import plotly.graph_objects as go

# 1. SEO & Page Config
st.set_page_config(page_title="Big Bot Investor | AI Stock Auditor", page_icon="📈")

st.title("🚀 MISSION: BIG BOT")
st.markdown("### AI-Powered Equity Auditor for the Indian Market")

# 2. Security: Checking for the Key in Secrets or Sidebar
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Gemini API Key to Unlock Brain", type="password")

if not api_key:
    st.warning("Please add your Gemini API Key to the Sidebar or Secrets to begin.")
    st.stop()

# Configure the AI
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# 3. The Watchlist (Added SBI, TCS, BEL, and Tata Motors)
ticker = st.selectbox("Select Stock for Audit", 
                     ["HDFCBANK.NS", "SBIN.NS", "TCS.NS", "BEL.NS", "TATAMOTORS.NS"])

# 4. Fetch Data & Display Chart
st.subheader(f"Technical Preview: {ticker}")
data = yf.download(ticker, period="1mo", interval="1d")

if not data.empty:
    # Creating a Candlestick Chart
    fig = go.Figure(data=[go.Candlestick(x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    name="Price Action")])
    fig.update_layout(height=400, template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    
    current_price = data['Close'].iloc[-1]
    st.metric(label="Current Price (NSE)", value=f"₹{current_price:,.2f}")

# 5. The Audit Button
if st.button("ACTIVATE AI AUDIT"):
    with st.spinner(f"Analyzing {ticker}..."):
        prompt = f"Provide a brief 2-sentence investment audit for {ticker} at its current price of ₹{current_price}. Focus on long-term outlook and market sentiment."
        response = model.generate_content(prompt)
        st.success(response.text)
