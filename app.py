import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
from PIL import Image
from datetime import datetime
import os
import time

# 1. PAGE CONFIG (Must be the very first Streamlit command)
st.set_page_config(
    page_title="Big Bot Investor | AI Stock Auditor", 
    page_icon="📈", 
    layout="wide"
)

# 2. GOOGLE SHEETS SETUP (The Secrets Way)
try:
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # CHANGE 1: Pull info from your Secrets box instead of a file
    creds_info = st.secrets["gcp_service_account"]
    
    # CHANGE 2: Use 'from_service_account_info' instead of '_file'
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    
    client = gspread.authorize(creds)
    sheet = client.open("My_Stock_Audits").sheet1 
except Exception as e:
    # If there's a typo in your Secrets, this error will tell you
    st.sidebar.error(f"Google Sheets Connection Error: {e}")

# 3. IDENTITY & SECURITY SETUP
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
model_flash = genai.GenerativeModel('gemini-flash-latest')
model_pro = genai.GenerativeModel(model_name='gemini-1.5-pro', system_instruction=SYSTEM_BEHAVIOR)

# --- HELPER FUNCTIONS ---

def log_audit_to_sheet(ticker, audit_text):
    """Saves the audit result to Google Sheets"""
    try:
        row = [datetime.now().strftime("%Y-%m-%d %H:%M"), ticker, audit_text[:500]]
        sheet.append_row(row)
    except:
        pass # Silently fail if sheets isn't connected

def chat_with_pro(user_input):
    """Handles the Chatbox logic (Text and Images)"""
    try:
        if "draw" in user_input.lower() or "image" in user_input.lower():
            response = model_pro.generate_content(user_input)
            if response.candidates[0].content.parts[0].inline_data:
                return response.candidates[0].content.parts[0].inline_data
            else:
                return "The AI couldn't generate the image. Try a different description!"
        else:
            response = model_pro.generate_content(user_input)
            return response.text
    except Exception as e:
        return f"Python Error: {str(e)}"

# --- MAIN APP UI ---

st.title("🚀 MISSION: BIG BOT")
st.markdown("### AI-Powered Equity Auditor for the Indian Market")

ticker = st.selectbox("Select Stock for Audit", 
                     ["HDFCBANK.NS", "SBIN.NS", "TCS.NS", "BEL.NS", "TATAMOTORS.NS"])

# Fetch Stock Data
data = yf.download(ticker, period="1mo", interval="1d")
if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

if not data.empty:
    current_price = float(data['Close'].iloc[-1])
    st.metric(label=f"Current Price ({ticker})", value=f"₹{current_price:,.2f}")

    fig = go.Figure(data=[go.Candlestick(
        x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close']
    )])
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=450)
    st.plotly_chart(fig, use_container_width=True)

    # THE AUDIT BUTTON
    if st.button("ACTIVATE AI AUDIT"):
        with st.spinner(f"Analyzing {ticker}..."):
            try:
                clean_price = str(round(float(current_price), 2))
                audit_prompt = f"Analyze {ticker} at {clean_price} INR. Give a 2-sentence long-term outlook."
                response = model_flash.generate_content(audit_prompt)
                
                if response.text:
                    st.success(f"**AI Insight:** {response.text}")
                    # --- NEW: SAVE TO GOOGLE SHEETS ---
                    log_audit_to_sheet(ticker, response.text)
                    st.info("Audit logged to Google Sheets!")
                else:
                    st.error("Empty response from AI.")
            except Exception as e:
                st.error(f"AI Error: {str(e)}")

else:
    st.warning("Data unavailable.")

# --- CHATBOX SECTION ---
st.divider()
st.subheader("🤖 Chat with Big Bot Pro")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about HDFC or 'Draw a bull market'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        result = chat_with_pro(prompt) 
        if isinstance(result, str):
            st.markdown(result)
            st.session_state.messages.append({"role": "assistant", "content": result})
        else:
            st.image(result)
            st.session_state.messages.append({"role": "assistant", "content": "Generated an image!"})
