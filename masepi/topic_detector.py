# topic_detector.py
# PURPOSE: Classify the user query into a known topic.
# NLP CONCEPT: Rule-based intent classification.
# Simple keyword matching — reliable, offline, explainable.

TOPIC_KEYWORDS = {
    "nic": [
        "හැඳුනුම්පත", "හැදුනුම්පත", "NIC", "nic",
        "ජාතික හැඳුනුම්පත", "identity", "හැදිනුම්",
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

DEFAULT_TOPIC = "general"


def detect_topic(user_input: str) -> str:
    """
    Two-pass detection:
    Pass 1 — exact phrase match (highest confidence)
    Pass 2 — keyword scoring (fallback)
    """
    user_lower = user_input.lower()

    # Pass 1: Exact high-confidence phrases
    if "හැඳුනුම්පත" in user_lower or " nic" in user_lower or user_lower.startswith("nic"):
        return "nic"
    if "ගමන් බලපත්‍රය" in user_lower or "passport" in user_lower:
        return "passport"
    if "රියදුරු" in user_lower or "driving" in user_lower or "ලයිසන්" in user_lower:
        return "driving_license"
    if "උප්පැන්න" in user_lower or "birth certificate" in user_lower:
        return "birth_certificate"

    # Pass 2: Keyword scoring
    scores = {topic: 0 for topic in TOPIC_KEYWORDS}
    for topic, keywords in TOPIC_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in user_lower:
                scores[topic] += 1

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else DEFAULT_TOPIC


def get_topic_display_name(topic: str) -> str:
    """Returns the Sinhala display name for a topic."""
    names = {
        "nic":               "ජාතික හැඳුනුම්පත",
        "passport":          "ගමන් බලපත්‍රය",
        "driving_license":   "රියදුරු බලපත්‍රය",
        "birth_certificate": "උප්පැන්න සහතිකය",
        "general":           "සාමාන්‍ය"
    }
    return names.get(topic, "සාමාන්‍ය")