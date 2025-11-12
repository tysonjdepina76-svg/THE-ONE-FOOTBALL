import streamlit as st
import os
from google import genai
from google.genai import types

# --- 1. UTILITY FUNCTION ---
def triple_reduction(value, reduction1=0.06, reduction2=0.07, reduction3=0.031):
    """Applies three consecutive reductions."""
    v = value * (1 - reduction1)
    v = v * (1 - reduction2)
    v = v * (1 - reduction3)
    return v

# --- 2. GEMINI API SETUP ---
@st.cache_resource
def setup_gemini_client():
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except KeyError:
        api_key = os.getenv("GEMINI_API_KEY") 
        if not api_key:
            st.error("GEMINI_API_KEY not found.")
            return None
    try:
        client = genai.Client(api_key=api_key)
        return client
    except Exception as e:
        st.error(f"Error initializing Gemini client: {e}")
        return None

@st.cache_resource
def start_chatbot_session(client):
    system_instruction = (
        "You are 'Prop-Bot', a highly analytical assistant specializing in NFL player prop betting. "
        "Provide analysis and high-confidence threshold picks."
    )
    chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction
        )
    )
    return chat

# --- 3. STREAMLIT UI AND CHAT MANAGEMENT ---
def main():
    st.set_page_config(page_title="Prop-Bot AI Agent", page_icon="🏈")
    st.title("🏈 Prop-Bot AI Agent")
    st.markdown("Your highly analytical assistant for NFL Player Prop Betting.")

    with st.sidebar:
        st.header("Prop-Bot Diagnostics")
        st.markdown("This bot uses the **Gemini AI** and a **custom triple-reduction model** for conservative projections.")
        st.subheader("⚠️ Deployment Status")
        if "GEMINI_API_KEY" in st.secrets:
             st.success("API Key Loaded! Ready for analysis.")
        else:
             st.warning("API Key Missing. Please check your secrets.")

    client = setup_gemini_client()
    if not client:
        return

    if "chat_session" not in st.session_state:
        st.session_state.chat_session = start_chatbot_session(client)
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm Prop-Bot. Ask me for a parlay pick or a game breakdown!"}
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask Prop-Bot about NFL props..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Prop-Bot is crunching the numbers..."):
            try:
                response = st.session_state.chat_session.send_message(prompt)
                with st.chat_message("assistant"):
                    st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Error communicating with Gemini. Error: {e}")

if __name__ == "__main__":
    main()
