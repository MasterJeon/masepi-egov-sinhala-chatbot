# retriever.py
# NLP CONCEPT: Section-aware RAG (Retrieval-Augmented Generation)
# Instead of sending the entire knowledge file (which overwhelms
# the LLM and causes hallucinations), we score each section
# against the user's query and return only the best matches.

import os

KNOWLEDGE_FILES = {
    "nic":               "knowledge/nic.txt",
    "passport":          "knowledge/passport.txt",
    "driving_license":   "knowledge/driving_license.txt",
    "birth_certificate": "knowledge/birth_certificate.txt",
}

GENERAL_CONTEXT = """
ශ්‍රී ලංකා රජයේ සේවා සහකාර හැඳින්වීම:
මෙම පද්ධතිය ශ්‍රී ලංකා රජයේ ප්‍රධාන ලේඛන සේවා පිළිබඳ
තොරතුරු ලබා දීම සඳහා නිර්මාණය කර ඇත.
ලබා ගත හැකි තොරතුරු: ජාතික හැඳුනුම්පත (NIC), ගමන් බලපත්‍රය,
රියදුරු බලපත්‍රය, උප්පැන්න සහතිකය.
ඔබට අවශ්‍ය සේවාව ගැන ප්‍රශ්නයක් කරන්න.
"""

# FIX: Expanded keywords — especially added location/where/one-day terms
# Q1 ("කොහේද" = where) was failing because "කොහේද" wasn't mapped anywhere
SECTION_KEYWORDS = {
    # NIC sections
    "පළමු වරට": [
        "පළමු", "first", "නව", "අලුත්", "ලබා ගැනීමට",
        "සුදුසුකම්", "eligib", "apply", "අයදුම්", "ගන්නේ", "ගන්න",
        "requirements", "documents", "ලේඛන"
    ],
    "අහිමි": [
        "අහිමි", "නැති", "lost", "නැතිවුණා", "replace",
        "ප්‍රතිස්ථාපන", "police", "පොලිස්", "duplicate"
    ],
    "සංශෝධනය": [
        "සංශෝධනය", "amend", "හානි", "වෙනස්", "incorrect",
        "wrong", "damage", "damaged", "broken", "illegible",
        "information", "නම", "name change", "married"
    ],
    "ඉක්මන් සාරාංශය": [
        # fees
        "ගාස්තු", "ගාස්තුව", "fee", "price", "cost", "රුපියල්", "කීයද",
        # location / where
        "කොහේද", "කොහෙද", "කොතැනද", "ස්ථාන", "location", "office",
        "කාර්යාල", "යන්", "go", "visit", "where", "address",
        # one-day service
        "එක් දින", "one day", "same day", "ශීඝ්‍ර", "1day",
        # battaramulla / galle
        "බත්තරමුල්ල", "ගාල්ල"
    ],
    # Passport sections
    "නව ගමන්": [
        "නව", "first", "first time", "ගන්න", "apply", "පළමු", "අලුත්",
        "documents", "ලේඛන", "requirements", "අවශ්‍ය"
    ],
    "ළමුන්": ["දරු", "ළමා", "child", "kids", "baby", "minor"],
    "ශීඝ්‍ර": [
        "ශීඝ්‍ර", "urgent", "fast", "quick", "ඉක්මන්", "3 day", "දින 3",
        "same day", "emergency"
    ],
    # Driving license sections
    "සාමාන්‍ය අවශ්‍යතා": [
        "ලේඛන", "documents", "requirements", "අවශ්‍ය", "bring",
        "medical", "වෛද්‍ය", "NTMI", "photograph", "ඡායාරූප", "NIC"
    ],
    "සැහැල්ලු": [
        "සැහැල්ලු", "light vehicle", "car", "රථය", "motor car",
        "17", "18", "learner", "L board", "ඉගෙනීමේ"
    ],
    "බර": [
        "බර", "heavy", "bus", "lorry", "ලොරි", "බස්", "20", "21",
        "height", "උස", "2 years", "වසර 2"
    ],
    "දිගු": [
        "දිගු", "extension", "add class", "additional", "adding",
        "extra", "extend"
    ],
    # Birth certificate sections
    "නිවසේ": [
        "නිවස", "home", "house", "ගෘහ", "B23", "ගෘහ ප්‍රසූතිය",
        "grama", "ග්‍රාම"
    ],
    "රෝහල්": [
        "රෝහල", "hospital", "maternity", "CR01", "medical",
        "ප්‍රසූතිය"
    ],
    "ප්‍රමාද": [
        "ප්‍රමාද", "late", "delay", "42", "3 months", "මාස 3",
        "one year", "වසරක්", "section 24"
    ],
    "ඉක්මන් සාරාංශ": [
        "ගාස්තු", "fee", "cost", "රු", "රුපියල්", "ස්ථාන", "office",
        "where", "කොහේද"
    ],
}


def _load_file(topic: str) -> str:
    file_path = KNOWLEDGE_FILES.get(topic)
    if not file_path:
        return ""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except (FileNotFoundError, UnicodeDecodeError) as e:
        print(f"[RETRIEVER WARNING] {e}")
        return ""


def _split_into_sections(text: str) -> list:
    """Split knowledge file on === dividers into (header, body) tuples."""
    raw_sections = text.split("===========================================")
    sections = []
    for chunk in raw_sections:
        chunk = chunk.strip()
        if not chunk:
            continue
        lines = chunk.splitlines()
        header = lines[0].strip() if lines else ""
        body   = "\n".join(lines).strip()
        sections.append((header, body))
    return sections


def _score_section(header: str, body: str, query: str) -> int:
    """
    Score section relevance to the user's query.
    Higher = more relevant.
    """
    query_lower = query.lower()
    score = 0

    # Check mapped section keywords
    for section_hint, keywords in SECTION_KEYWORDS.items():
        # Check if this section_hint matches the header or first line
        if section_hint in header or section_hint in body[:80]:
            for kw in keywords:
                if kw.lower() in query_lower:
                    score += 4  # Strong match: section + keyword aligned

    # Count raw word hits in body (weaker signal)
    body_lower = body.lower()
    for word in query_lower.split():
        if len(word) > 2 and word in body_lower:
            score += 1

    return score


def get_context(topic: str, user_query: str = "") -> str:
    """
    Returns the most relevant SECTION(S) from the knowledge file.
    
    Always includes the summary section (fees, locations) if it exists,
    because most follow-up questions are about fees or where to go.
    """
    if topic == "general" or topic not in KNOWLEDGE_FILES:
        return GENERAL_CONTEXT

    full_text = _load_file(topic)
    if not full_text:
        return GENERAL_CONTEXT

    # No query = return full file (backward compatible)
    if not user_query.strip():
        return full_text

    sections    = _split_into_sections(full_text)
    scored      = []
    summary_sec = None

    for header, body in sections:
        # Always grab the summary/quick-reference section separately
        if "සාරාංශය" in header or "Quick" in header or "Reference" in header or "ඉක්මන්" in header:
            summary_sec = body
            continue
        s = _score_section(header, body, user_query)
        scored.append((s, header, body))

    # Top 2 most relevant sections
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:2]

    parts = [body.strip() for _, _, body in top if body.strip()]
    if summary_sec:
        parts.append(summary_sec.strip())

    return "\n\n---\n\n".join(parts) if parts else full_text


def list_available_topics() -> list:
    return [t for t, p in KNOWLEDGE_FILES.items() if os.path.exists(p)]
