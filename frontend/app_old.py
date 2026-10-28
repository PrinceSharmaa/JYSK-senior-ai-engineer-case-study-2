import os

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://localhost:8000",
)

st.set_page_config(
    page_title="SheetPilot AI",
    page_icon="📊",
    layout="wide",
)

st.title("📊 SheetPilot AI")
st.caption(
    "An intelligent Excel assistant powered by Gemini"
)

st.divider()

# Backend connection
st.subheader("Backend Connection")

try:
    response = httpx.get(
        f"{BACKEND_URL}/health",
        timeout=5.0,
    )
    response.raise_for_status()

    st.success("Backend connected successfully!")

except httpx.HTTPError:
    st.error(
        "Backend unavailable. "
        "Please start the FastAPI server."
    )

st.divider()

# File upload interface
st.subheader("Upload Spreadsheet")

uploaded_file = st.file_uploader(
    "Choose an Excel or CSV file",
    type=["xlsx", "xlsm", "csv", "tsv"],
)

if uploaded_file is not None:
    st.success(
        f"Selected file: {uploaded_file.name}"
    )

    st.info(
        "File processing will be implemented "
        "in Phase 2."
    )

st.divider()

# Chat interface
st.subheader("Chat With Your Spreadsheet")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

prompt = st.chat_input(
    "Ask me something about your spreadsheet..."
)

if prompt:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.write(prompt)

    assistant_message = (
        "The AI agent will be connected "
        "in a later phase."
    )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": assistant_message,
        }
    )

    with st.chat_message("assistant"):
        st.write(assistant_message)