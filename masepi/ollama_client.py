# ollama_client.py
# -------------------------------------------------------
# PURPOSE: All communication with the local Ollama server.
#
# KEY CONCEPT: Ollama runs as a local HTTP server on your
# machine (port 11434). We call it using Python's `requests`
# library — same as calling any REST API, but it's all LOCAL.
# No data ever leaves your machine. That's what makes this
# truly offline.
# -------------------------------------------------------

import requests
import json

# Ollama server address — always localhost for offline use
OLLAMA_BASE_URL = "http://localhost:11434"

# Model priority: try llama3.1 first, fall back to mistral
PRIMARY_MODEL = "llama3.1"
FALLBACK_MODEL = "mistral"

# Request timeout in seconds — important for UX
# If Ollama takes too long, we don't want the UI to freeze
TIMEOUT_SECONDS = 120


def check_ollama_running() -> bool:
    """
    Ping Ollama to check if it's online.
    Call this at app startup to give a clear error message
    rather than letting the app crash mysteriously later.
    """
    try:
        response = requests.get(
            f"{OLLAMA_BASE_URL}/api/tags",
            timeout=5
        )
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def get_available_models() -> list:
    """
    Fetch the list of models Ollama has downloaded locally.
    Useful for checking which models are available before
    attempting inference.
    """
    try:
        response = requests.get(
            f"{OLLAMA_BASE_URL}/api/tags",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
    except Exception:
        pass
    return []


def select_model() -> str:
    """
    Pick the best available model.
    Returns PRIMARY_MODEL if available, else FALLBACK_MODEL,
    else the first available model.

    WHY: We can't assume the user has pulled llama3.1.
    This makes the app resilient.
    """
    available = get_available_models()

    # Check for primary (check if model name starts with our target
    # because Ollama appends ":latest" e.g. "llama3.1:latest")
    for model in available:
        if PRIMARY_MODEL in model:
            return model

    for model in available:
        if FALLBACK_MODEL in model:
            return model

    # Last resort: use whatever is installed
    if available:
        return available[0]

    # Nothing found — return primary and let Ollama give the error
    return PRIMARY_MODEL


def generate_response(messages: list, model: str = None) -> str:
    """
    Send a chat request to Ollama and get a response.

    Args:
        messages: List of {"role": ..., "content": ...} dicts
                  (built by prompt_builder.py)
        model: Which model to use (auto-selected if None)

    Returns:
        The model's response text (string)

    IMPORTANT: We use /api/chat (not /api/generate).
    /api/chat supports multi-turn conversation with history.
    /api/generate is simpler but doesn't handle history well.
    """
    if model is None:
        model = select_model()

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,        # Get complete response at once
        "options": {
            "temperature": 0.3,  # Lower = more focused/consistent
            # Why 0.3? For a government info chatbot, we want
            # ACCURATE answers, not creative ones.
            # Range: 0.0 (robotic) to 1.0 (creative/unpredictable)
            "num_predict": 512,  # Max tokens to generate
            # 512 is enough for most government service answers
            # without wasting compute time
        }
    }

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=TIMEOUT_SECONDS
        )

        if response.status_code == 200:
            data = response.json()
            # Extract the text from Ollama's response structure
            return data["message"]["content"].strip()

        else:
            error_text = response.text[:200]  # Truncate long errors
            return f"දෝෂයක් ඇති විය (Error {response.status_code}): {error_text}"

    except requests.exceptions.ConnectionError:
        return ("Ollama සේවාදායකය සම්බන්ධ කර ගත නොහැක. "
                "කරුණාකර 'ollama serve' ධාවනය කර ඇති බව පරීක්ෂා කරන්න.")

    except requests.exceptions.Timeout:
        return ("ප්‍රතිචාරය ලබා ගැනීමට කාලය ඉකුත් විය. "
                "ආදර්ශය (model) ධාවනය වෙමින් තිබිය හැකිය. "
                "කරුණාකර නැවත උත්සාහ කරන්න.")

    except Exception as e:
        return f"අනපේක්ෂිත දෝෂයක්: {str(e)}"


def generate_with_fallback(messages: list) -> tuple[str, str]:
    """
    Try the primary model first, fall back to secondary on failure.

    Returns:
        (response_text, model_used)
    
    This gives the UI info about which model was used,
    which you can display for transparency.
    """
    primary = None
    fallback = None

    available = get_available_models()
    for m in available:
        if PRIMARY_MODEL in m and primary is None:
            primary = m
        if FALLBACK_MODEL in m and fallback is None:
            fallback = m

    # Try primary model
    if primary:
        result = generate_response(messages, model=primary)
        if not result.startswith("දෝෂයක්") and not result.startswith("Ollama"):
            return result, primary

    # Fall back to secondary
    if fallback:
        result = generate_response(messages, model=fallback)
        return result, fallback

    # Nothing worked
    return ("ස්ථාපිත ආදර්ශ කිසිවක් සොයා ගත නොහැක. "
            "'ollama pull llama3.1' ධාවනය කරන්න."), "none"