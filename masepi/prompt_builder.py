# prompt_builder.py
# -------------------------------------------------------
# PURPOSE: Construct a well-structured prompt for Ollama
#          that reliably produces Sinhala responses.
#
# NLP CONCEPT: PROMPT ENGINEERING
# The LLM doesn't "know" it should respond in Sinhala
# unless you tell it clearly and repeatedly. 
# Key techniques used here:
#   1. System prompt (sets the persona and rules)
#   2. Context injection (RAG output goes here)
#   3. Explicit language instruction (MUST respond in Sinhala)
#   4. Few-shot examples (optional, but improves consistency)
#   5. Chat history inclusion (for memory)
#   6. Clear formatting of the final question
# -------------------------------------------------------


#def build_system_prompt() -> str:
#    """
#    The system prompt runs ONCE at the start of every request.
#    It tells the model WHO it is and HOW it must behave.

#    KEY INSIGHT: Repeating "Sinhala" multiple times is
 #   intentional — LLMs respond to emphasis. One mention
 #   is often ignored, especially for non-English languages.
 #   """
 #   return """ඔබ "Masepi" — ශ්‍රී ලංකා රජයේ ලේඛන සේවා සඳහා විශේෂඥ සහකාරයෙකි.

#ඔබේ ප්‍රධාන නීති:
#1. ඔබ සෑම විටම සිංහල භාෂාවෙන් පමණක් පිළිතුරු දිය යුතුය.
#2. ඔබ ශ්‍රී ලංකා රජයේ නිල ක්‍රියාපටිපාටි ගැන නිවැරදි තොරතුරු ලබා දිය යුතුය.
#3. ඔබ ලබා දුන් සන්දර්භය (context) පදනම් කරගෙන පිළිතුරු දිය යුතුය.
#4. ඔබ නොදන්නා දෙයක් ගැන ප්‍රශ්නයක් ඇසුවහොත්, "මට ඒ ගැන නිශ්චිත තොරතුරු නැත" යනුවෙන් සිංහලෙන් ඇහිව කියන්න.
#5. ඔබ කිසිදු ඉංග්‍රීසි වචනයක් භාවිතා නොකළ යුතුය, හැකි සෑම විටම.
#6. ඔබේ පිළිතුරු කෙටි, පැහැදිලි, හා ප්‍රයෝජනවත් විය යුතුය.

#ඔබ "Masepi" — You are a Sri Lankan government services assistant. ALWAYS respond in Sinhala only."""

def build_system_prompt() -> str:
    """
    The system prompt runs ONCE at the start of every request.
    """
    return """System Role: Masepi - Sri Lankan Government Services Assistant.

Rules:
1. You MUST generate your final response entirely in the Sinhala language (සිංහල).
2. NEVER output English translations unless explicitly requested.
3. Base your answers ONLY on the provided context. If the answer is not in the context, say: "මට ඒ ගැන නිශ්චිත තොරතුරු නැත."
4. Format your output clearly using bullet points if needed, but keep the text in Sinhala.

සිංහල භාෂාවෙන් පමණක් පිළිතුරු සපයන්න."""

def build_prompt(user_query: str, context: str, chat_history: list) -> list:
    """
    Builds the full message list to send to Ollama.

    Args:
        user_query: The current Sinhala question from the user
        context: Retrieved knowledge base text (from retriever.py)
        chat_history: List of {"role": "user"/"assistant", "content": "..."} dicts

    Returns:
        A list of message dicts in Ollama chat format

    WHY THIS FORMAT?
    Ollama's /api/chat endpoint uses the same format as OpenAI:
    a list of {"role": ..., "content": ...} messages.
    This lets the model see the full conversation history,
    which is what gives it "memory" within a session.
    """

    messages = []

    # 1. System message — sets the model's persona
    system_content = build_system_prompt()
    messages.append({
        "role": "system",
        "content": system_content
    })

    # 2. Include recent chat history (last 6 turns = 3 exchanges)
    # WHY LIMIT? Sending too much history wastes tokens and
    # can confuse the model. 3 exchanges is usually enough
    # for conversational context.
    recent_history = chat_history[-6:] if len(chat_history) > 6 else chat_history
    for message in recent_history:
        messages.append(message)

    # 3. Build the current user turn with context injected
    # This is the core of RAG: we prepend the retrieved
    # knowledge to the user's actual question.
    user_message_content = f"""පහත සන්දර්භය (context) භාවිතා කරමින් ප්‍රශ්නයට සිංහලෙන් පිළිතුරු දෙන්න:

--- සන්දර්භය (Context) ---
{context}
--- සන්දර්භය අවසන් ---

පරිශීලකයාගේ ප්‍රශ්නය: {user_query}

වැදගත්: ඔබේ සම්පූර්ණ පිළිතුර සිංහල භාෂාවෙන් විය යුතුය."""

    messages.append({
        "role": "user",
        "content": user_message_content
    })

    return messages


def build_greeting() -> str:
    """Returns the chatbot's initial greeting in Sinhala."""
    return """ආයුබෝවන්! මම Masepi — ශ්‍රී ලංකා රජයේ ලේඛන සේවා සහකාරයා.

මට ඔබට මෙම කරුණු ගැන සිංහලෙන් සහය දිය හැකිය:
📋 ජාතික හැඳුනුම්පත (NIC)
✈️ ගමන් බලපත්‍රය (Passport)  
🚗 රියදුරු බලපත්‍රය (Driving License)
📜 උප්පැන්න සහතිකය (Birth Certificate)

ඔබේ ප්‍රශ්නය සිංහලෙන් ඇසීමට ආරාධනා කරමි! 🙏"""