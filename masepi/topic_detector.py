# topic_detector.py
# -------------------------------------------------------
# PURPOSE: Classify the user's query into one of our
#          known topic categories using keyword matching.
#
# NLP CONCEPT: This is a simple "intent detection" or 
# "topic classification" module. Real systems use ML 
# models, but keyword matching is reliable, offline,
# and explainable — perfect for this project.
# -------------------------------------------------------

# Each topic maps to a list of Sinhala AND English keywords.
# Why both? Users might mix languages (code-switching),
# and having English fallbacks makes it more robust.

TOPIC_KEYWORDS = {
    "nic": [
        # Sinhala keywords
        "හැඳුනුම්පත", "හැදුනුම්පත", "NIC", "nic",
        "ජාතික හැඳුනුම්පත", "identity", "හැදිනුම්",
        # Common misspellings / variants
        "හැනිදුම්", "id card"
    ],
    "passport": [
        "ගමන් බලපත්‍රය", "ගමන් බලපත්රය", "passport",
        "Passport", "විදේශ", "travel", "visa",
        "ගමන්", "බලපත්‍ර"
    ],
    "driving_license": [
        "රියදුරු බලපත්‍රය", "රියදුරු", "driving",
        "license", "licence", "ලයිසන්", "රිය",
        "වාහන", "motor", "L board", "L බෝඩ්"
    ],
    "birth_certificate": [
        "උප්පැන්න", "ඉපදීම", "birth", "certificate",
        "සහතිකය", "දරුවා", "ලියාපදිංචිය", "registry",
        "රෙජිස්ට්‍රාර්"
    ]
}

# Default response topic when nothing matches
DEFAULT_TOPIC = "general"


def detect_topic(user_input: str) -> str:
    """
    Scan the user's message for keywords and return the
    best matching topic. Returns DEFAULT_TOPIC if no match.

    Why lowercase? Sinhala unicode is case-consistent, but
    any Latin characters the user types might be mixed case.
    """
    user_lower = user_input.lower()

    # Score each topic by how many keywords appear
    scores = {topic: 0 for topic in TOPIC_KEYWORDS}

    for topic, keywords in TOPIC_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in user_lower:
                scores[topic] += 1

    # Pick the highest-scoring topic
    best_topic = max(scores, key=scores.get)

    # Only return it if at least one keyword matched
    if scores[best_topic] > 0:
        return best_topic

    return DEFAULT_TOPIC


def get_topic_display_name(topic: str) -> str:
    """Human-readable Sinhala name for each topic (for UI display)."""
    names = {
        "nic": "ජාතික හැඳුනුම්පත",
        "passport": "ගමන් බලපත්‍රය",
        "driving_license": "රියදුරු බලපත්‍රය",
        "birth_certificate": "උප්පැන්න සහතිකය",
        "general": "සාමාන්‍ය"
    }
    return names.get(topic, "සාමාන්‍ය")