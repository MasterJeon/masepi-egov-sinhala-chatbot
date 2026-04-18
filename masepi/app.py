# app.py
# Main Streamlit UI for Masepi chatbot.
# FLOW: User types → topic_detector → retriever (section)
#       → prompt_builder → ollama_client → display

import streamlit as st
from topic_detector import detect_topic, get_topic_display_name
from retriever import get_context
from prompt_builder import build_prompt, build_greeting
from ollama_client import check_ollama_running, generate_with_fallback, get_available_models

# ── Page config — MUST be first Streamlit call ──────────
st.set_page_config(
    page_title="Masepi — සිංහල රජය සේවා",
    page_icon="🇱🇰",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ── CSS — FULLY OFFLINE (no Google Fonts CDN) ───────────
# FIX: Removed @import url('https://fonts.googleapis.com/...')
# That caused a network request every page load — breaking
# offline operation and violating the assignment constraint.
# Windows 10/11 ships with Nirmala UI which renders Sinhala
# correctly. We fall back to system sans-serif fonts.
st.markdown("""
<style>
    .sinhala-text {
        font-family: 'Nirmala UI', 'Iskoola Pota', 'Arial Unicode MS', sans-serif;
        font-size: 16px;
        line-height: 1.9;
    }
    .topic-badge {
        background-color: #1a5276;
        color: white;
        padding: 3px 12px;
        border-radius: 12px;
        font-size: 13px;
        font-family: 'Nirmala UI', sans-serif;
        display: inline-block;
        margin-top: 6px;
    }
    .stChatMessage p {
        font-family: 'Nirmala UI', 'Iskoola Pota', sans-serif;
        font-size: 16px;
        line-height: 1.9;
    }
</style>
""", unsafe_allow_html=True)


# ── Session State ────────────────────────────────────────
# Streamlit reruns the entire script on every interaction.
# session_state is how we persist data across reruns.

if "messages"       not in st.session_state:
    st.session_state.messages       = []   # Chat display history
if "ollama_history" not in st.session_state:
    st.session_state.ollama_history = []   # API message history
if "model_used"     not in st.session_state:
    st.session_state.model_used     = "Unknown"
if "initialized"    not in st.session_state:
    st.session_state.initialized    = False
if "ollama_status"  not in st.session_state:
    # FIX: Cache the ollama status so we only check ONCE per session
    # Previously it was checked on every page rerender — slow on Windows
    st.session_state.ollama_status  = None


# ── Check Ollama once per session ───────────────────────
def get_ollama_status() -> bool:
    """Check and cache Ollama status in session state."""
    if st.session_state.ollama_status is None:
        st.session_state.ollama_status = check_ollama_running()
    return st.session_state.ollama_status


# ── Sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.title("🇱🇰 මා.සේ.පී")
    st.caption("මහජන සේවය පිණිසයි!")
    st.divider()

    st.subheader("⚙️ පද්ධති තත්ත්වය")
    ollama_ok = get_ollama_status()

    if ollama_ok:
        st.success("✅ Ollama: සක්‍රිය")
        models = get_available_models()
        if models:
            st.info(f"📦 {', '.join(models[:2])}")
        else:
            st.warning("⚠️ ආදර්ශ ස්ථාපිත නැත")
    else:
        st.error("❌ Ollama: ක්‍රියා විරහිත")
        st.markdown("**නව terminal එකක් විවෘත කර:**")
        st.code("ollama serve", language="bash")

    st.divider()

    st.subheader("සේවා ලැයිස්තුව")
    st.markdown("""
<div class="sinhala-text">
📋 ජාතික හැඳුනුම්පත (NIC)<br>
✈️ ගමන් බලපත්‍රය<br>
🚗 රියදුරු බලපත්‍රය<br>
📜 උප්පැන්න සහතිකය
</div>
""", unsafe_allow_html=True)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ මකන්න", use_container_width=True):
            st.session_state.messages       = []
            st.session_state.ollama_history = []
            st.session_state.initialized    = False
            st.session_state.ollama_status  = None  # Re-check on next load
            st.rerun()
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.ollama_status = None
            st.rerun()

    if st.session_state.model_used != "Unknown":
        st.caption(f"🤖 {st.session_state.model_used}")


# ── Main Chat Area ───────────────────────────────────────
st.title("🇱🇰 මා.සේ.පී")
st.markdown(
    "<p class='sinhala-text' style='color: #666; font-size: 18px; margin-top: -15px; margin-bottom: 20px;'>රජයේ සේවා සඳහා ඔබේ සිංහල ඩිජිටල් මඟපෙන්වන්නා</p>",
    unsafe_allow_html=True
)

# Show greeting on first load
if not st.session_state.initialized:
    st.session_state.messages.append({
        "role": "assistant",
        "content": build_greeting()
    })
    st.session_state.initialized = True

# ── Render chat history ──────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(
            f"<div class='sinhala-text'>{msg['content']}</div>",
            unsafe_allow_html=True
        )
        if "topic" in msg and msg["topic"] != "general":
            st.markdown(
                f"<span class='topic-badge'>🏷️ {get_topic_display_name(msg['topic'])}</span>",
                unsafe_allow_html=True
            )


# ── Handle user input ────────────────────────────────────
if prompt := st.chat_input("ඔබේ ප්‍රශ්නය සිංහලෙන් ටයිප් කරන්න..."):

    # Verify Ollama is up before proceeding
    if not get_ollama_status():
        st.error("Ollama ක්‍රියා නොකරයි. 'ollama serve' ධාවනය කරන්න.")
        st.stop()

    # Show user message
    with st.chat_message("user"):
        st.markdown(
            f"<div class='sinhala-text'>{prompt}</div>",
            unsafe_allow_html=True
        )

    # ── NLP Pipeline ─────────────────────────────────────

    # Step 1: Intent/Topic Detection
    detected_topic = detect_topic(prompt)

    # Step 2: Topic continuity — if user asks a follow-up
    # question with no topic keywords (e.g. "ගාස්තුව කීයද?"),
    # inherit the topic from the previous message
    if detected_topic == "general" and len(st.session_state.messages) > 1:
        for prev in reversed(st.session_state.messages):
            if prev.get("topic", "general") != "general":
                detected_topic = prev["topic"]
                break

    # Step 3: Section-aware RAG retrieval
    # KEY FIX: We now pass the user's query so the retriever
    # can return only the RELEVANT SECTION, not the full file.
    # This is what prevents hallucinations.
    context = get_context(detected_topic, user_query=prompt)

    # Step 4: Build structured prompt with history
    ollama_messages = build_prompt(
        user_query=prompt,
        context=context,
        chat_history=st.session_state.ollama_history
    )

    # Step 5: Generate and display response
    with st.chat_message("assistant"):
        with st.spinner("Masepi සිතමින් සිටී... 🤔"):
            response_text, model_used = generate_with_fallback(ollama_messages)

        st.session_state.model_used = model_used
        st.markdown(
            f"<div class='sinhala-text'>{response_text}</div>",
            unsafe_allow_html=True
        )
        if detected_topic != "general":
            st.markdown(
                f"<span class='topic-badge'>🏷️ {get_topic_display_name(detected_topic)}</span>",
                unsafe_allow_html=True
            )

    # Step 6: Update histories
    st.session_state.messages.append({"role": "user",      "content": prompt, "topic": detected_topic})
    st.session_state.messages.append({"role": "assistant", "content": response_text, "topic": detected_topic})

    st.session_state.ollama_history.append({"role": "user",      "content": prompt})
    st.session_state.ollama_history.append({"role": "assistant", "content": response_text})

    # Keep last 10 exchanges (20 messages) to avoid context overflow
    if len(st.session_state.ollama_history) > 20:
        st.session_state.ollama_history = st.session_state.ollama_history[-20:]