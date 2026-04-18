# prompt_builder.py
# PURPOSE: Build structured prompts for the Ollama LLM.
# The quality of answers depends almost entirely on prompt design.

def build_system_prompt() -> str:
    return """You are 'Masepi', a highly accurate Sri Lankan Government Services Assistant.
Your ONLY job is to answer the user's question using the provided CONTEXT.

CRITICAL RULES:
1. You MUST write your final response ENTIRELY in Sinhala (සිංහල). Do not output any English words.
2. Read the CONTEXT carefully. Extract the exact facts. Do not invent or guess information.
3. If the answer is NOT explicitly written in the CONTEXT, you MUST reply with exactly this phrase and nothing else: "මට ඒ ගැන නිශ්චිත තොරතුරු නැත."
4. FEES AND NUMBERS: Only state a fee or number if it is LITERALLY written in the CONTEXT. Copy it exactly. Do NOT use any fee from your training memory.
5. If a question asks about something outside Sri Lankan government document services, reply only: "මට ඒ ගැන නිශ්චිත තොරතුරු නැත."
6. Keep your Sinhala sentences short, professional, and grammatically correct. Do not cut off mid-sentence."""

def build_prompt(user_query: str, context: str, chat_history: list) -> list:
    """
    Builds the Ollama /api/chat message list.
    Structure: [system] → [recent history] → [context + question]
    """
    messages = []

    messages.append({
        "role": "system",
        "content": build_system_prompt()
    })

    # Last 3 exchanges = 6 messages.
    # Too much history makes the model forget its rules.
    recent = chat_history[-6:] if len(chat_history) > 6 else chat_history
    for msg in recent:
        messages.append(msg)

    # Reading-comprehension format: CONTEXT → QUESTION → ANSWER IN SINHALA
    # This is the most reliable format for fact extraction from LLaMA 3.1.
    # The "SINHALA ANSWER:" suffix acts as a strong completion cue.


    # Reading-comprehension format: CONTEXT → QUESTION → ANSWER IN SINHALA
    user_content = f"""CONTEXT (answer ONLY from what is written here):
    {context}

    QUESTION: {user_query}

    Pay special attention to sections labelled "විශේෂ ලේඛන නීති" for special cases like age 50+ without birth certificate. Write a short factual answer in Sinhala prose sentences. No bullet points. No dashes. If the answer is not explicitly in the CONTEXT, write only: මට ඒ ගැන නිශ්චිත තොරතුරු නැත.

    SINHALA ANSWER:"""

    messages.append({
        "role": "user",
        "content": user_content
    })

    return messages


def build_greeting() -> str:
    return """<h3 style="margin-bottom: 2px;"><b>ආයුබෝවන්! මම MaSePi.</b> 🙏</h3>
<p style="color: #555; font-size: 16px; margin-top: 0px; margin-bottom: 15px; font-style: italic;">"මහජන සේවය පිණිසයි"</p>

රජයේ සේවාවන් ලබාගැනීමේදී ඔබට අවශ්‍ය නිවැරදි මඟ පෙන්වීම ඉතා පහසුවෙන් ලබා දීම මගේ අරමුණයි.<br><br>

පහත සඳහන් සේවාවන් සඳහා ඔබට අවශ්‍ය තොරතුරු මාගෙන් අසන්න:<br>

<div style="font-size: 19px; font-weight: 600; line-height: 1.8; margin-top: 10px; margin-bottom: 15px; padding-left: 15px; border-left: 3px solid #1a5276;">
📋 ජාතික හැඳුනුම්පත (NIC)<br>
✈️ ගමන් බලපත්‍රය (Passport)<br>
🚗 රියදුරු බලපත්‍රය (Driving License)<br>
📜 උප්පැන්න සහතිකය (Birth Certificate)
</div>

ඔබට අද දැනගැනීමට අවශ්‍ය කුමක්ද? ඔබේ ප්‍රශ්නය සිංහලෙන් ඇසීමට ආරාධනා කරමි! 😊"""