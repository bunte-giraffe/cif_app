# gemini_streamlit_app.py
import streamlit as st
import google.generativeai as genai
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
PASSWORD = os.getenv("APP_PASSWORD", "demo123")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash-001")
else:
    model = None

# Approximate token pricing
PRICE_PER_1K_INPUT = 0.00025
PRICE_PER_1K_OUTPUT = 0.0005

# Predefined roles and missions
PREDEFINED = {
    "English Teacher": [
        "Prepare a lesson about friends and family",
        "Teach numbers from 1 to 10 with fun activities"
    ],
    "Philosophical Guide": [
        "Help someone grieving the loss of a loved one",
        "Explain the concept of free will"
    ],
    "Coding Tutor": [
        "Explain the basics of Python to a beginner",
        "Guide a student through a simple web scraping project"
    ]
}

# Token counting (rough estimation)
def count_tokens(text):
    return max(len(text.split()), 1)  # very basic approximation

# Session state init
def init_state():
    if "history" not in st.session_state:
        st.session_state.history = []
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "admin" not in st.session_state:
        st.session_state.admin = False

# Auth page
def auth_page():
    st.title("🔒 Login")
    name = st.text_input("Your name or alias")
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if pw == PASSWORD:
            st.session_state.authenticated = True
            st.session_state.user = name
        elif pw == ADMIN_PASSWORD:
            st.session_state.authenticated = True
            st.session_state.admin = True
            st.session_state.user = name
        else:
            st.error("Incorrect password")

# Admin backend
def admin_page():
    st.title("🔧 Admin Panel")
    st.subheader("API Key")
    st.code(GEMINI_API_KEY or "Not set")
    st.subheader("Prompt/Response Logs")
    for i, item in enumerate(st.session_state.history):
        st.markdown(f"**{i+1}. Prompt**: {item['prompt']}")
        st.markdown(f"**Response**: {item['response']}")
        st.markdown(f"**Input tokens**: {item['input_tokens']}, Output tokens: {item['output_tokens']}, Cost: ${item['cost']:.5f}")
        st.markdown("---")

# Main chat interface
def chat_interface():
    st.title("🧠 Gemini Custom GPT")
    st.write(f"Welcome, **{st.session_state.user}**")

    with st.sidebar:
        st.header("Custom Instructions")

        predefined_role = st.selectbox("Choose a predefined role", ["--"] + list(PREDEFINED.keys()))
        if predefined_role != "--":
            role = predefined_role
            mission = st.selectbox("Choose a mission", PREDEFINED[role])
        else:
            role = st.text_input("Role (required)")
            mission = st.text_input("Mission (required)")

        extra = st.text_area("Additional instructions (optional)")

    if not role or not mission:
        st.warning("Please fill in both required fields: role and mission")
        return

    system_instructions = f"You are a {role}. Your mission is to {mission}."
    if extra:
        system_instructions += f" {extra}"

    st.text_area("System Instructions", system_instructions, height=100, disabled=True)

    user_message = st.text_input("Your message")
    if st.button("Send") and user_message and model:
        full_prompt = f"{system_instructions}\nUser: {user_message}\nAssistant:"
        with st.spinner("Thinking..."):
            response = model.generate_content(full_prompt)
            output_text = response.text

        input_tokens = count_tokens(full_prompt)
        output_tokens = count_tokens(output_text)
        cost = (input_tokens / 1000 * PRICE_PER_1K_INPUT) + (output_tokens / 1000 * PRICE_PER_1K_OUTPUT)

        st.markdown("**Gemini says:**")
        st.write(output_text)
        st.markdown(f"*Input tokens*: {input_tokens}, *Output tokens*: {output_tokens}, *Cost*: **${cost:.5f}**")

        # Save interaction
        st.session_state.history.append({
            "prompt": full_prompt,
            "response": output_text,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost,
            "timestamp": datetime.now().isoformat()
        })

# App flow
init_state()
if not st.session_state.authenticated:
    auth_page()
elif st.session_state.admin:
    admin_page()
else:
    chat_interface()
