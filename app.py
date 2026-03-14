import google.generativeai as genai
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# NOW you can use st.set_page_config (ONLY ONCE)
st.set_page_config(
    page_title="Big Bot Investor | AI Stock Auditor", 
    page_icon="📈", 
    layout="wide"
)

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
# This will automatically pick Gemini 3 Flash today, and Gemini 4 next year!
model = genai.GenerativeModel('gemini-flash-latest')
# 3. The Watchlist (Added SBI, TCS, BEL, and Tata Motors)
ticker = st.selectbox("Select Stock for Audit", 
                     ["HDFCBANK.NS", "SBIN.NS", "TCS.NS", "BEL.NS", "TATAMOTORS.NS"])

# Function for Nano Banana Pro Chat/Generation
def chat_with_pro(user_input):
    # We use the 'model' we already configured at the top of your script
    # If the user asks for a visual, we use the Pro model
    if "draw" in user_input.lower() or "image" in user_input.lower():
        # Using the standard library's way of calling the Pro model
        pro_model = genai.GenerativeModel('gemini-3-pro-image-preview')
        response = pro_model.generate_content(user_input)
        
        # In this library, we check if there's an image in the parts
        return response.candidates[0].content.parts[0].inline_data
    else:
        # Regular chat using the high-speed Flash brain
        # This uses the 'model' variable you already defined on line 28
        response = model.generate_content(user_input)
        return response.text

# 4. Fetch Data and Display Chart
data = yf.download(ticker, period="1mo", interval="1d")

# Fix for the 2026 Multi-Index column issue
if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

if not data.empty:
    # 5. Show Metric
    current_price = float(data['Close'].iloc[-1])
    st.metric(label=f"Current Price ({ticker})", value=f"₹{current_price:,.2f}")

    # 6. Build Professional Chart
    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close']
    )])
    
    fig.update_layout(
        template="plotly_dark", 
        xaxis_rangeslider_visible=False,
        height=450,
        margin=dict(l=10, r=10, t=30, b=10)
    )
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Data is currently unavailable for this ticker.")  
    
# 5. The Audit Button (Bulletproof Version)
if st.button("ACTIVATE AI AUDIT"):
    if not api_key:
        st.error("Please enter your API Key in the sidebar first!")
    else:
        with st.spinner(f"Analyzing {ticker}..."):
            try:
                # We turn the price into a simple string to avoid the InvalidArgument error
                clean_price = str(round(float(current_price), 2))
                
                # A very clear, simple prompt for the AI
                audit_prompt = f"Analyze the stock {ticker} currently trading at {clean_price} INR. Give a 2-sentence long-term outlook."
                
                # Execute the AI call
                response = model.generate_content(audit_prompt)
                
                if response.text:
                    st.success(f"**AI Insight:** {response.text}")
                else:
                    st.error("The AI returned an empty response. Try again.")
                    
            except Exception as e:
                # This will tell us exactly what is wrong if it fails again
                st.error(f"AI Error: {str(e)}")

# --- START OF NEW CHATBOX CODE ---
st.divider()
st.subheader("🤖 Chat with Big Bot Pro")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input box
if prompt := st.chat_input("Ask Big Bot a question or 'Draw a bull market'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # This calls the function we added earlier
        result = chat_with_pro(prompt) 
        if isinstance(result, str):
            st.markdown(result)
            st.session_state.messages.append({"role": "assistant", "content": result})
        else:
            st.image(result)
            st.session_state.messages.append({"role": "assistant", "content": "Generated an image!"})
# --- END OF NEW CHATBOX CODE ---
