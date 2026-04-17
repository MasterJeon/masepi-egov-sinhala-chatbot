# retriever.py
# -------------------------------------------------------
# PURPOSE: Load the correct knowledge file based on the
#          detected topic, and return relevant context.
#
# NLP CONCEPT: RAG = Retrieval-Augmented Generation.
# Instead of relying only on what the LLM "knows" from
# training, we RETRIEVE facts from our local files and
# AUGMENT the prompt with that context. This makes the
# chatbot accurate and domain-specific.
#
# Our RAG is "naive" (full-document retrieval) which is
# perfectly fine for small knowledge bases like ours.
# -------------------------------------------------------

import os

# Map topics to their knowledge file paths
KNOWLEDGE_FILES = {
    "nic": "knowledge/nic.txt",
    "passport": "knowledge/passport.txt",
    "driving_license": "knowledge/driving_license.txt",
    "birth_certificate": "knowledge/birth_certificate.txt",
}

# Fallback context when no topic matches
GENERAL_CONTEXT = """
ශ්‍රී ලංකා රජයේ සේවා සහකාර හැඳින්වීම:
මෙම පද්ධතිය ශ්‍රී ලංකා රජයේ ප්‍රධාන ලේඛන සේවා පිළිබඳ 
තොරතුරු ලබා දීම සඳහා නිර්මාණය කර ඇත.

ලබා ගත හැකි තොරතුරු:
- ජාතික හැඳුනුම්පත (NIC)
- ගමන් බලපත්‍රය (Passport)
- රියදුරු බලපත්‍රය (Driving License)
- උප්පැන්න සහතිකය (Birth Certificate)

ඔබට අවශ්‍ය සේවාව ගැන ප්‍රශ්නයක් කරන්න.
"""


def get_context(topic: str) -> str:
    """
    Load and return the full text of the knowledge file
    for a given topic.

    Why full-document? Our files are small (< 1000 words each).
    For larger knowledge bases, you'd split into chunks and
    use semantic search (embedding similarity). That's 
    "advanced RAG" — this is "basic RAG".
    """
    if topic == "general" or topic not in KNOWLEDGE_FILES:
        return GENERAL_CONTEXT

    file_path = KNOWLEDGE_FILES[topic]

    # Always use try/except for file I/O — files can be missing,
    # corrupted, or have wrong encoding. UTF-8 is essential for
    # Sinhala unicode text.
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        if not content:
            return GENERAL_CONTEXT

        return content

    except FileNotFoundError:
        print(f"[RETRIEVER WARNING] File not found: {file_path}")
        return GENERAL_CONTEXT

    except UnicodeDecodeError:
        print(f"[RETRIEVER WARNING] Encoding error in: {file_path}")
        return GENERAL_CONTEXT


def list_available_topics() -> list:
    """Returns topics that have actual knowledge files present."""
    available = []
    for topic, path in KNOWLEDGE_FILES.items():
        if os.path.exists(path):
            available.append(topic)
    return available