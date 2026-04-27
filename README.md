# 🇱🇰 MaSepi — මා.සේ.පී
### *මහජන සේවය පිණිය*
**An Offline Sinhala Conversational Agent for Sri Lankan Government Services**

---

## 📌 What is MaSepi?

**MaSepi** (මා.සේ.පී — *මහජන සේවය පිණිය* / "For the Benefit of Public Service") is a fully offline, Sinhala-language chatbot that helps Sri Lankan citizens navigate government document services. It accepts natural Sinhala input and responds with accurate, grounded Sinhala answers — **without any internet connection**.

The chatbot covers four government service domains:

| Domain | Sinhala | Covers |
|---|---|---|
| 📋 National Identity Card | ජාතික හැඳුනුම්පත | Eligibility, fees, lost NIC, amendments |
| ✈️ Passport | ගමන් බලපත්‍රය | Application, biometrics, offices, validity |
| 🚗 Driving License | රියදුරු බලපත්‍රය | Light/heavy vehicle, age rules, NTMI |
| 📜 Birth Certificate | උප්පැන්න සහතිකය | Home/hospital birth, late registration |

---

## 🎬 Demo Video

▶️ **[Watch Full Demo on YouTube](https://youtu.be/DDa9-tbszuo)**

> Recorded with WiFi fully disabled — demonstrates complete offline operation, Ollama running locally, Streamlit UI, and Sinhala conversations across all 4 domains.

---

## ⚙️ System Architecture

MaSepi follows a **3-layer architecture**:
┌────────────────────────────────────────────┐
│ LAYER 1 — Streamlit UI (app.py) │
│ Chat input, bubbles, topic badge, │
│ sidebar status, session history │
└──────────────────┬─────────────────────────┘
│ user query
┌──────────────────▼─────────────────────────┐
│ LAYER 2 — NLP Processing Core │
│ topic_detector.py → intent detection │
│ retriever.py → RAG context load │
│ prompt_builder.py → prompt assembly │
│ ollama_client.py → HTTP API client │
└──────────────────┬─────────────────────────┘
│ structured prompt
┌──────────────────▼─────────────────────────┐
│ LAYER 3 — LLM Inference │
│ Ollama runtime → localhost:11434 │
│ LLaMA 3.1 (8B) → local model weights │
│ knowledge/ → 4 × .txt files (RAG) │
└────────────────────────────────────────────┘

text

### NLP Pipeline (per user message)
User Input → topic_detector.py → retriever.py → prompt_builder.py → ollama_client.py → Sinhala Response

text

1. **Intent Detection** — Two-pass keyword classification (exact match → keyword scoring)
2. **Context Continuity** — Inherits previous topic for follow-up questions
3. **RAG Retrieval** — Loads relevant local `.txt` knowledge file
4. **Prompt Construction** — System rules + history (last 6 turns) + context + question
5. **LLM Generation** — LLaMA 3.1 via Ollama, `temperature=0.0` for factual consistency
6. **Display + History Update** — Response shown with topic badge; session state updated

---

## 🗂️ Project Structure
masepi/
│
├── app.py # Main Streamlit UI
├── topic_detector.py # Two-pass keyword intent classifier
├── retriever.py # RAG — loads local knowledge files
├── prompt_builder.py # Prompt assembly with Sinhala enforcement rules
├── ollama_client.py # Ollama HTTP API client with model fallback
│
└── knowledge/
├── nic.txt # NIC domain knowledge (Sinhala, UTF-8)
├── passport.txt # Passport domain knowledge
├── driving_license.txt # Driving license domain knowledge
└── birth_certificate.txt # Birth certificate domain knowledge

text

---

## 🚀 Getting Started

### Prerequisites

- Windows 10/11
- Python 3.10+
- [Ollama](https://ollama.com) installed locally

### Step 1 — Install Ollama and pull the model

```bash
# Install Ollama from https://ollama.com
# Then pull LLaMA 3.1:
ollama pull llama3.1
```

### Step 2 — Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/masepi-egov-sinhala-chatbot.git
cd masepi-egov-sinhala-chatbot
```

### Step 3 — Set up virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
```

### Step 4 — Install dependencies

```bash
pip install streamlit requests
```

### Step 5 — Start Ollama

```bash
ollama serve
```

### Step 6 — Run the app

```bash
cd masepi
streamlit run app.py
```

Open your browser at `http://localhost:8501` 🎉

---

## 🔌 Offline Operation

MaSepi is **fully offline** by design. Every component runs locally:

| Component | Technology | How it's Offline |
|---|---|---|
| Language Model | LLaMA 3.1 (8B) | Stored in `~/.ollama/models/` |
| LLM Runtime | Ollama | Runs on `localhost:11434` |
| Knowledge Base | 4 × `.txt` files | Stored in `knowledge/` folder |
| Web Interface | Streamlit | Runs on `localhost:8501` |
| Fonts | Nirmala UI / Iskoola Pota | Native Windows system fonts |
| Python Packages | pip | Pre-installed, no runtime downloads |

No data ever leaves your machine.

---

## 🧠 Key NLP Concepts Used

| Concept | Where Used |
|---|---|
| **RAG** (Retrieval-Augmented Generation) | `retriever.py` — local `.txt` files as knowledge base |
| **Intent Detection** | `topic_detector.py` — two-pass keyword classification |
| **Prompt Engineering** | `prompt_builder.py` — hybrid English rules + Sinhala output enforcement |
| **Context Window Management** | `app.py` — trims history to last 20 messages |
| **Hallucination Prevention** | System prompt rules 2, 3, 4 — context-only answers |
| **Unicode Handling** | `retriever.py` — `encoding="utf-8"` for Sinhala script (U+0D80–U+0DFF) |

---

## 💬 Example Conversations
User: අහිමි වූ හැඳුනුම්පතක් ලබා ගැනීමට ගාස්තුව කීයද?
Masepi: අහිමි වූ ජාතික හැඳුනුම්පත වෙනුවට නව NIC නිකුත් කිරීම
සඳහා ගාස්තුව රුපියල් 1000 කි.
🏷️ ජාතික හැඳුනුම්පත

text
User: ඇමරිකාවට වීසා ගන්නේ කොහොමද?
Masepi: මට ඒ ගැන නිශ්චිත තොරතුරු නැත.
🏷️ සාමාන්‍ය

text

---

## 🛠️ Tech Stack

- **Language Model:** LLaMA 3.1 8B (via Ollama)
- **LLM Runtime:** [Ollama](https://ollama.com)
- **Frontend:** [Streamlit](https://streamlit.io)
- **Language:** Python 3.10+
- **NLP Approach:** Rule-based intent detection + naive full-document RAG
- **Sinhala Encoding:** Unicode block U+0D80–U+0DFF, UTF-8

---

## ⚠️ Known Limitations

- Uses naive full-document RAG — not chunk-based semantic search
- Procedural/multi-step questions may yield incomplete answers
- Heavily misspelled Sinhala may miss keyword detection
- Model performance depends on hardware (LLaMA 3.1 8B requires ~8GB RAM)

---

## 📚 References

1. Meta AI. (2024). *LLaMA 3.1 — Open Foundation and Fine-Tuned Chat Models.* https://ollama.com/library/llama3.1
2. Ollama. (2024). *Run LLMs Locally.* https://ollama.com
3. Streamlit Inc. (2024). *Streamlit Documentation.* https://docs.streamlit.io
4. Lewis, P., et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.* arXiv:2005.11401
5. Unicode Consortium. (2023). *Sinhala Block U+0D80–U+0DFF.*

---
