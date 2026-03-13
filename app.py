import streamlit as st
import yfinance as yf
import google.generativeai as genai

# 1. Page Config
st.set_page_config(page_title="BIG BOT Investor", page_icon="🚀")
st.title("🚀 MISSION: BIG BOT")

# 2. Sidebar for Security
st.sidebar.header("Security")
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

if api_key:
    # Configure Gemini
    genai.configure(api_key=api_key)
    ai_model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')

    # 3. User Inputs
    ticker = st.selectbox("Select Stock", ['HDFCBANK.NS', 'SBIN.NS', 'BEL.NS', 'TCS.NS'])
    
    if st.button("ACTIVATE AUDIT"):
        with st.spinner("Analyzing Market Data..."):
            stock = yf.Ticker(ticker)
            price = stock.fast_info['lastPrice']
            
            # AI Prompt
            prompt = f"As a professional analyst in 2026, evaluate {ticker} at ₹{price:.2f}. Is it a buy for long-term? 2 sentences max."
            response = ai_model.generate_content(prompt)
            
            st.metric(label="Live Price", value=f"₹{price:.2f}")
            st.success(f"**AI Insight:** {response.text}")
else:
    st.warning("Please enter your API Key in the sidebar to unlock the brain.")
