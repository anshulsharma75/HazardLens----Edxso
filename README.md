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

## 🎥 Video Walkthrough

 [Watch Demo Video](https://drive.google.com/file/d/180qr-mXiKmX-KNUY2_q_AwzMjlvxzZAs/view?usp=drivesdk)  ← (click to watch video)



## 🌐 Live Application

 https://hazardlens.streamlit.app ← (click to access the live demo)
HazardLens

Visual risk assessment for field inspections. Upload a photo of a site or asset, record the inspection context, and HazardLens produces a quantified risk register, a 5×5 risk matrix, a prioritised corrective-action plan and a downloadable PDF inspection report.

Live app: https://hazardlens.streamlit.app/

Why it exists

Routine safety walk-downs rely on inspectors noticing and documenting hazards consistently. HazardLens turns a single photograph into a structured, auditable assessment (the same format used in EHS risk registers) in seconds, so hazards are captured, scored and tracked to closure instead of living in a chat message.

Features
Area	Capability
Assessment	Multimodal vision analysis with a strict JSON schema, scene-type aware
Risk engine	Deterministic 5×5 likelihood × severity scoring, bands and 0–100 risk index
Evidence	Annotated image with numbered hazard markers on a 3×3 locator grid
Actions	Prioritised corrective-action plan (P1/P2/P3) with owner and timeframe
Reporting	PDF inspection report, Markdown, JSON, CSV register export
Workflow	Inspection register with status tracking (Open / In progress / Closed)
Analytics	Dashboard: KPIs, rating distribution, hazard categories, portfolio risk matrix, trend
Follow-up	Ask further questions about the same image
Languages	English, Hindi, Hinglish
Reliability	Automatic model fallback chain, JSON repair, input validation, unit tests, CI
Architecture
Streamlit pagesviews.py
imaging.pyprepare + annotate
ai.pyGroq vision + fallback
risk.pynormalise + 5x5 scoring
report.pyPDF / Markdown
state.pysession records
HazardLens/
├── app.py                  # entrypoint: navigation + engine settings
├── hazardlens/
│   ├── config.py           # constants, models, enums
│   ├── ai.py               # Groq client, prompts, fallback, JSON parsing (UI-free)
│   ├── risk.py             # 5x5 matrix, normalisation, risk index (UI-free)
│   ├── imaging.py          # preprocessing + hazard-zone annotation
│   ├── report.py           # PDF + Markdown report builders
│   ├── state.py            # session-scoped records
│   ├── views.py            # dashboard / inspection / register / methodology pages
│   └── ui/                 # design system (CSS) + HTML components
├── tests/                  # pytest unit tests
└── .github/workflows/ci.yml

The model only describes hazards and proposes likelihood/severity (1–5). Scores, bands and the risk index are computed in risk.py, so identical ratings always give identical results.

Methodology

score = likelihood × severity → 1–4 Low · 5–9 Medium · 10–14 High · 15–25 Critical. risk index = top score / 25 × 100, plus a small uplift (max 8) for additional hazards.

Run locally
bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # add your GROQ_API_KEY
streamlit run app.py
pytest -q
Deploy (Streamlit Community Cloud)
Push this repository to GitHub.
Create the app with main file path app.py.
In Settings → Secrets add GROQ_API_KEY = "gsk_...".
Limitations
Advisory output from a single photo; it can miss hazards or misjudge severity.
Hazard locations are approximate (3×3 grid), not pixel-accurate detection.
Referenced standards are suggestions and must be verified.
Records live only in the visitor's session (no shared storage by design, for privacy).
Roadmap

Persistent per-user storage (Supabase/Postgres) · authentication · video frame analysis · bounding-box detection · offline PWA for field use · multi-site dashboards.

Disclaimer

Not a substitute for a qualified safety professional. In real danger call local emergency services (112 in India).
