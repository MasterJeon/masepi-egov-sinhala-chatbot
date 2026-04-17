# app.py
# -------------------------------------------------------
# PURPOSE: Main Streamlit application — the user interface.
#
# ARCHITECTURE FLOW (what happens on each message):
#   User types → topic_detector → retriever → prompt_builder
#                                                    ↓
#              Streamlit displays ← ollama_client ←──┘
#
# HOW TO RUN:
#   streamlit run app.py
# -------------------------------------------------------

import streamlit as st
from topic_detector import detect_topic, get_topic_display_name
from retriever import get_context
from prompt_builder import build_prompt, build_greeting
from ollama_client import (
    check_ollama_running,
    generate_with_fallback,
    get_available_models
)

# ── Page Configuration ──────────────────────────────────
# This MUST be the first Streamlit command in the script
st.set_page_config(
    page_title="Masepi — සිංහල රජය සේවා",
    page_icon="🇱🇰",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ── Custom CSS for Sinhala font support ─────────────────
# Why: Default Streamlit fonts may not render Sinhala
# Unicode properly on all systems. We explicitly load
# Noto Sans Sinhala from Google Fonts.
# NOTE: If you need FULL offline, download the font file
# and serve it locally. For the demo, this one CDN call
# is acceptable (disable if truly offline testing).
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Sinhala:wght@400;600&display=swap');
    
    .sinhala-text {
        font-family: 'Noto Sans Sinhala', sans-serif;
        font-size: 16px;
        line-height: 1.8;
    }
    
    .topic-badge {
        background-color: #1a5276;
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 13px;
        font-family: 'Noto Sans Sinhala', sans-serif;
    }
    
    .stChatMessage {
        font-family: 'Noto Sans Sinhala', sans-serif;
    }
</style>
""", unsafe_allow_html=True)


# ── Session State Initialization ────────────────────────
# Streamlit re-runs the entire script on every interaction.
# st.session_state persists data between those re-runs.
# This is how we implement "chat memory" in Streamlit.

if "messages" not in st.session_state:
    # messages = the actual chat history shown in the UI
    st.session_state.messages = []

if "ollama_history" not in st.session_state:
    # ollama_history = the message list sent to Ollama API
    # (includes system prompts, context etc.)
    st.session_state.ollama_history = []

if "model_used" not in st.session_state:
    st.session_state.model_used = "Unknown"

if "initialized" not in st.session_state:
    st.session_state.initialized = False


# ── Sidebar ─────────────────────────────────────────────
with st.sidebar:
    st.title("🇱🇰 Masepi")
    st.caption("ශ්‍රී ලංකා රජය සේවා සහකාරයා")
    
    st.divider()
    
    # System Status
    st.subheader("⚙️ පද්ධති තත්ත්වය")
    
    ollama_ok = check_ollama_running()
    
    if ollama_ok:
        st.success("✅ Ollama: සක්‍රිය")
        available_models = get_available_models()
        if available_models:
            st.info(f"📦 Models: {', '.join(available_models[:3])}")
        else:
            st.warning("⚠️ ආදර්ශ ස්ථාපිත නැත")
    else:
        st.error("❌ Ollama: ක්‍රියා විරහිත")
        st.code("ollama serve", language="bash")
        st.caption("ඉහත විධානය ධාවනය කරන්න")
    
    st.divider()
    
    # Topic Guide
    st.subheader("📋 සේවා ලැයිස්තුව")
    st.markdown("""
    <div class="sinhala-text">
    📋 ජාතික හැඳුනුම්පත<br>
    ✈️ ගමන් බලපත්‍රය<br>
    🚗 රියදුරු බලපත්‍රය<br>
    📜 උප්පැන්න සහතිකය
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Clear chat button
    if st.button("🗑️ කතාබස් මකන්න", use_container_width=True):
        st.session_state.messages = []
        st.session_state.ollama_history = []
        st.session_state.initialized = False
        st.rerun()
    
    # Model info
    if st.session_state.model_used != "Unknown":
        st.caption(f"🤖 Model: {st.session_state.model_used}")


# ── Main Chat Area ───────────────────────────────────────
st.title("🇱🇰 Masepi")
st.markdown(
    "<p class='sinhala-text'>ශ්‍රී ලංකා රජය ලේඛන සේවා - සිංහල සහකාරයා</p>",
    unsafe_allow_html=True
)

# Show greeting on first load
if not st.session_state.initialized:
    greeting = build_greeting()
    st.session_state.messages.append({
        "role": "assistant",
        "content": greeting
    })
    st.session_state.initialized = True

# ── Render Chat History ──────────────────────────────────
# Loop through all stored messages and display them.
# Streamlit's st.chat_message automatically styles
# user vs assistant messages differently.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(
            f"<div class='sinhala-text'>{message['content']}</div>",
            unsafe_allow_html=True
        )
        # Show topic badge if it was detected for this message
        if "topic" in message:
            topic_name = get_topic_display_name(message["topic"])
            st.markdown(
                f"<span class='topic-badge'>🏷️ {topic_name}</span>",
                unsafe_allow_html=True
            )


# ── Handle User Input ────────────────────────────────────
# st.chat_input creates the text box at the bottom.
# It returns the user's text when they press Enter.
if prompt := st.chat_input("ඔබේ ප්‍රශ්නය සිංහලෙන් ටයිප් කරන්න..."):

    # Check Ollama is running before proceeding
    if not check_ollama_running():
        st.error(
            "Ollama ක්‍රියා නොකරයි. 'ollama serve' ධාවනය කරන්න."
        )
        st.stop()

    # 1. Display the user's message immediately
    with st.chat_message("user"):
        st.markdown(
            f"<div class='sinhala-text'>{prompt}</div>",
            unsafe_allow_html=True
        )

    # 2. Detect the topic (NLP step 1)
    detected_topic = detect_topic(prompt)

    # 3. Retrieve relevant context (RAG step)
    context = get_context(detected_topic)

    # 4. Build the structured prompt
    # We pass ollama_history (not messages) to keep track
    # of what Ollama has seen (system prompts etc.)
    ollama_messages = build_prompt(
        user_query=prompt,
        context=context,
        chat_history=st.session_state.ollama_history
    )

    # 5. Generate response with spinner (so user knows it's thinking)
    with st.chat_message("assistant"):
        with st.spinner("Masepi සිතමින් සිටී... 🤔"):
            response_text, model_used = generate_with_fallback(ollama_messages)

        st.session_state.model_used = model_used

        # Display the response
        st.markdown(
            f"<div class='sinhala-text'>{response_text}</div>",
            unsafe_allow_html=True
        )
        # Show which topic was detected
        topic_name = get_topic_display_name(detected_topic)
        st.markdown(
            f"<span class='topic-badge'>🏷️ {topic_name}</span>",
            unsafe_allow_html=True
        )

    # 6. Update chat history for display
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text,
        "topic": detected_topic
    })

    # 7. Update Ollama history (raw format for API)
    # We store ONLY user and assistant roles here (not system),
    # because the system prompt is rebuilt fresh each request
    st.session_state.ollama_history.append({
        "role": "user",
        "content": prompt
    })
    st.session_state.ollama_history.append({
        "role": "assistant",
        "content": response_text
    })

    # 8. Keep history manageable — trim to last 10 exchanges
    if len(st.session_state.ollama_history) > 20:
        st.session_state.ollama_history = st.session_state.ollama_history[-20:]
