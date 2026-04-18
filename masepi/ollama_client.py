# ollama_client.py
# Handles all communication with the local Ollama server.
# Ollama runs as a local HTTP server on port 11434.
# No data ever leaves the machine — fully offline.

import requests

OLLAMA_BASE_URL = "http://localhost:11434"
PRIMARY_MODEL   = "llama3.1"
FALLBACK_MODEL  = "mistral"
TIMEOUT_SECONDS = 180  # 3 minutes — large models can be slow on first run


def check_ollama_running() -> bool:
    """
    Ping Ollama. Returns True if reachable, False for ANY error.
    FIX: Now catches ALL exceptions (ConnectionError, ReadTimeout, etc.)
    The original code only caught ConnectionError — ReadTimeout caused crashes.
    """
    try:
        response = requests.get(
            f"{OLLAMA_BASE_URL}/api/tags",
            timeout=30  # 30s — Windows can be slow to respond
        )
        return response.status_code == 200
    except Exception:
        # Catches ConnectionError, ReadTimeout, JSONDecodeError — everything
        return False


def get_available_models() -> list:
    """Returns list of locally installed model names."""
    try:
        response = requests.get(
            f"{OLLAMA_BASE_URL}/api/tags",
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        pass
    return []


def select_model() -> str:
    """
    Picks the best available model.
    Prefers llama3.1, falls back to mistral, then whatever is installed.
    """
    available = get_available_models()
    for m in available:
        if PRIMARY_MODEL in m:
            return m
    for m in available:
        if FALLBACK_MODEL in m:
            return m
    if available:
        return available[0]
    return PRIMARY_MODEL


def generate_response(messages: list, model: str = None) -> str:
    """
    Sends chat messages to Ollama and returns the response text.
    Uses /api/chat for proper multi-turn conversation support.
    """
    if model is None:
        model = select_model()

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.0,    # Zero creativity — facts only
            "top_p": 1.0,
            "num_predict": 400,
            "repeat_penalty": 1.1  # Prevents repetition (fixes Q4-style bug)
        }
    }

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=TIMEOUT_SECONDS
        )
        if response.status_code == 200:
            return response.json()["message"]["content"].strip()
        else:
            return f"දෝෂයක් ඇති විය (Error {response.status_code})"

    except requests.exceptions.ConnectionError:
        return "Ollama සේවාදායකය සම්බන්ධ කර ගත නොහැක. 'ollama serve' ධාවනය කරන්න."
    except requests.exceptions.Timeout:
        return "ප්‍රතිචාරය ලබා ගැනීමට කාලය ඉකුත් විය. නැවත උත්සාහ කරන්න."
    except Exception as e:
        return f"අනපේක්ෂිත දෝෂයක්: {str(e)}"


def generate_with_fallback(messages: list) -> tuple:
    """
    Tries primary model first, falls back to mistral.
    Returns (response_text, model_name_used).
    """
    available = get_available_models()
    primary  = next((m for m in available if PRIMARY_MODEL  in m), None)
    fallback = next((m for m in available if FALLBACK_MODEL in m), None)

    error_prefixes = ("දෝෂයක්", "Ollama", "ප්‍රතිචාරය", "අනපේක්ෂිත")

    if primary:
        result = generate_response(messages, model=primary)
        if not any(result.startswith(p) for p in error_prefixes):
            return result, primary

    if fallback:
        result = generate_response(messages, model=fallback)
        return result, fallback

    return "ස්ථාපිත ආදර්ශ කිසිවක් සොයා ගත නොහැක. 'ollama pull llama3.1' ධාවනය කරන්න.", "none"