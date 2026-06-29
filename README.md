# HazardLens — Multimodal AI Assistant
### Edxso AI Engineer Intern — Assignment 2

> **Author:** Anshul Kumar 
> **Stack:** `Groq LLaMA 3.2 Vision` · `Streamlit` · `Pillow`

---

## What This Does

A multimodal AI assistant that accepts an image + a natural language query and returns a **contextual danger analysis** — not a generic caption, but a specific, actionable safety warning grounded in what the image actually shows.

**Assignment scenario tested:**
- Image: frayed electrical cord lying next to a puddle of water
- Query: *"What is the primary danger shown in this image?"*
- Output: Specific electrocution hazard warning with reasoning

---

## Architecture

```
User uploads image + types query
            ↓
   Image encoded to base64
            ↓
  Groq LLaMA 3.2 Vision (11B)
  [image + query + system prompt]
            ↓
  Contextual danger inferred
            ↓
  Hazard / Safe UI response
```

---

## Quick Start

```bash
git clone https://github.com/anshulsharma75/hazardlens
cd hazardlens
pip install -r requirements.txt
streamlit run app.py
```

Set your Groq API key in the sidebar (get one free at console.groq.com).

---

## Design Decisions

| Decision | Why |
|---|---|
| **LLaMA 3.2 Vision via Groq** | Free, fast, strong vision reasoning — no OpenAI cost |
| **System prompt as safety expert** | Forces contextual danger inference, not just captioning |
| **Base64 image encoding** | Works without any file storage or cloud upload |
| **Danger keyword detection** | Auto-switches UI between red warning and green safe states |
| **Streamlit UI** | Minimal setup, runs locally, easy to demo in video |

---

## File Structure

```
.
├── app.py             # Main Streamlit application
├── requirements.txt
└── README.md
```

---

## Video Walkthrough

🎥 [Link to async demo video](#) ← *(add after recording)*

## 🌐 Live Deployed Application

🔗 Link to deployed application

