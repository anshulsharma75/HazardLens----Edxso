"""
HazardLens AI - Visual hazard detection, risk scoring & safety reports.
Stack: Streamlit + Groq vision models (Qwen 3.x) + Pillow + Pandas + ReportLab
"""
import base64
import html
import io
import json
import re
from datetime import datetime

import httpx
import pandas as pd
import streamlit as st
from groq import Groq
from PIL import Image, ImageOps

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="HazardLens AI", page_icon="⚡", layout="wide")

# Order matters: if one model is retired/unavailable, the next one is tried.
# (llama-4-scout was retired by Groq on 17 Jul 2026 -> that caused the 404.)
MODELS = {
    "Qwen 3.8 · 27B (Recommended)": "qwen/qwen3.8-27b",
    "Qwen 3.6 · 27B": "qwen/qwen3.6-27b",
    "Muse Spark Open": "meta-models/muse-spark-open",
}
CONTEXTS = ["General", "Road & Traffic", "Construction Site", "Industrial / Factory",
            "Home & Household", "Fire & Electrical", "Flood / Water Leak", "Public Place"]
LANGUAGES = ["English", "Hindi (हिन्दी)", "Hinglish"]
DEPTHS = ["Quick (top 3 hazards)", "Detailed (up to 8 hazards)"]
PRESETS = [
    "⚡ Quick questions...",
    "What is the primary danger shown in this image?",
    "List every safety hazard and rate its severity.",
    "Is it safe for people to be near this? What should they do?",
    "What could go wrong if this is ignored for 24 hours?",
    "Who should I call and what should I do right now?",
]
SEV_ORDER = ["Low", "Medium", "High", "Critical"]
SEV_COLOR = {"Low": "#22c55e", "Medium": "#eab308", "High": "#f97316", "Critical": "#ef4444"}
SEV_SCORE = {"Low": 15, "Medium": 40, "High": 70, "Critical": 90}
CATEGORIES = ["Electrical", "Fire", "Structural", "Chemical", "Traffic", "Water", "Biological", "Mechanical", "Other"]

# ─────────────────────────────────────────────────────────────────────────────
# STYLE
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] { background:#020408 !important; font-family:'Inter',sans-serif; color:#e8eaf0; }
[data-testid="stAppViewContainer"] {
  background: radial-gradient(ellipse 80% 50% at 50% -10%, rgba(220,38,38,0.15) 0%, transparent 70%),
              radial-gradient(ellipse 50% 40% at 90% 90%, rgba(239,68,68,0.08) 0%, transparent 60%), #020408 !important; }
[data-testid="stHeader"], [data-testid="stToolbar"], section[data-testid="stSidebar"], footer, #MainMenu { display:none !important; }
[data-testid="stMainBlockContainer"], .block-container { padding:0 0 24px 0 !important; max-width:100% !important; }
.stDeployButton { display:none; }
label[data-testid="stWidgetLabel"] { color:#64748b !important; font-size:12px !important; }

.hero { text-align:center; padding:64px 24px 36px; }
.hero-badge { display:inline-flex; align-items:center; gap:8px; background:rgba(220,38,38,0.12);
  border:1px solid rgba(220,38,38,0.3); border-radius:100px; padding:6px 16px; font-size:11px; font-weight:600;
  letter-spacing:2px; text-transform:uppercase; color:#f87171; margin-bottom:26px; }
.hero-badge .dot { width:6px; height:6px; background:#ef4444; border-radius:50%; animation:pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1);} 50%{opacity:.4;transform:scale(.8);} }
.hero h1 { font-family:'Space Grotesk',sans-serif; font-size:clamp(46px,7vw,86px); font-weight:700; line-height:1;
  letter-spacing:-3px; color:#fff; margin:0 0 18px 0; padding:0; }
.hero h1 span { background:linear-gradient(135deg,#ef4444 0%,#f97316 50%,#fbbf24 100%);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.hero-sub { font-size:17px; color:#64748b; max-width:560px; margin:0 auto 40px; line-height:1.6; }
.stats-row { display:flex; justify-content:center; gap:32px; margin-bottom:44px; flex-wrap:wrap; }
.stat-item { text-align:center; }
.stat-num { font-family:'Space Grotesk',sans-serif; font-size:28px; font-weight:700; color:#fff; line-height:1; }
.stat-label { font-size:11px; color:#475569; letter-spacing:1px; text-transform:uppercase; margin-top:4px; }
.stat-divider { width:1px; background:#1e2430; align-self:stretch; }

[data-testid="stTabs"] { padding:0 40px; }
button[data-baseweb="tab"] { font-weight:600 !important; }

.st-key-maincard { background:linear-gradient(135deg,rgba(255,255,255,0.04),rgba(255,255,255,0.01));
  border:1px solid rgba(255,255,255,0.08); border-radius:24px; padding:32px; margin:12px 0 24px;
  box-shadow:0 0 0 1px rgba(255,255,255,0.04),0 32px 64px rgba(0,0,0,0.6),0 0 80px rgba(220,38,38,0.06),inset 0 1px 0 rgba(255,255,255,0.08); }
.section-label { font-size:10px; font-weight:700; letter-spacing:2.5px; text-transform:uppercase; color:#475569; margin:6px 0 10px; }

[data-testid="stFileUploader"] section { background:rgba(255,255,255,0.02) !important; border:1.5px dashed rgba(255,255,255,0.12) !important; border-radius:16px !important; }
[data-testid="stFileUploader"] section:hover { border-color:rgba(239,68,68,0.45) !important; background:rgba(239,68,68,0.03) !important; }
.stTextArea textarea, .stTextInput input { background:rgba(255,255,255,0.03) !important; border:1px solid rgba(255,255,255,0.08) !important;
  border-radius:12px !important; color:#e2e8f0 !important; font-size:15px !important; }
.stTextArea textarea:focus, .stTextInput input:focus { border-color:rgba(239,68,68,0.5) !important; box-shadow:0 0 0 3px rgba(239,68,68,0.08) !important; }
.stButton > button, .stDownloadButton > button { background:linear-gradient(135deg,#dc2626,#b91c1c) !important; color:#fff !important; border:none !important;
  border-radius:14px !important; padding:14px 28px !important; font-size:15px !important; font-weight:600 !important; width:100% !important;
  box-shadow:0 4px 16px rgba(220,38,38,0.35),0 1px 0 rgba(255,255,255,0.1) inset !important; transition:all .2s !important; }
.stButton > button:hover, .stDownloadButton > button:hover { background:linear-gradient(135deg,#ef4444,#dc2626) !important;
  box-shadow:0 8px 24px rgba(220,38,38,0.5) !important; transform:translateY(-1px) !important; }
[data-testid="stImage"] img { border-radius:14px !important; border:1px solid rgba(255,255,255,0.08) !important; box-shadow:0 16px 40px rgba(0,0,0,0.5) !important; }

.result-danger { background:linear-gradient(135deg,rgba(220,38,38,0.1),rgba(185,28,28,0.06)); border:1px solid rgba(220,38,38,0.35);
  border-radius:18px; padding:26px 30px; margin:8px 0 18px; box-shadow:0 0 40px rgba(220,38,38,0.08),inset 0 1px 0 rgba(255,255,255,0.05); }
.result-safe { background:linear-gradient(135deg,rgba(34,197,94,0.08),rgba(21,128,61,0.05)); border:1px solid rgba(34,197,94,0.3);
  border-radius:18px; padding:26px 30px; margin:8px 0 18px; box-shadow:0 0 40px rgba(34,197,94,0.06); }
.result-tag { display:inline-flex; align-items:center; gap:6px; font-size:10px; font-weight:700; letter-spacing:2px; text-transform:uppercase;
  margin-bottom:12px; padding:5px 12px; border-radius:100px; }
.tag-danger { background:rgba(220,38,38,0.2); color:#f87171; border:1px solid rgba(220,38,38,0.3); }
.tag-safe { background:rgba(34,197,94,0.15); color:#4ade80; border:1px solid rgba(34,197,94,0.3); }
.result-title { font-family:'Space Grotesk',sans-serif; font-size:26px; font-weight:700; color:#fff; margin-bottom:8px; }
.result-text { font-size:15.5px; line-height:1.75; color:#e2e8f0; }

.tile { background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07); border-radius:16px; padding:18px 14px; text-align:center; height:100%; }
.tile-v { font-family:'Space Grotesk',sans-serif; font-size:30px; font-weight:700; line-height:1.1; }
.tile-l { font-size:10px; color:#64748b; letter-spacing:1.5px; text-transform:uppercase; margin-top:6px; }
.gauge { height:10px; border-radius:99px; background:rgba(255,255,255,0.07); overflow:hidden; margin:14px 0 4px; }
.gauge-fill { height:100%; border-radius:99px; }

.hz { background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07); border-radius:14px; padding:16px 18px; margin-bottom:12px; }
.hz-top { display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:8px; }
.sev { font-size:10px; font-weight:800; letter-spacing:1.5px; padding:3px 10px; border-radius:99px; text-transform:uppercase; }
.cat { font-size:10px; font-weight:600; letter-spacing:1px; padding:3px 10px; border-radius:99px; color:#94a3b8; border:1px solid rgba(255,255,255,0.1); text-transform:uppercase; }
.hz-name { font-weight:700; color:#fff; font-size:16px; }
.hz-desc { color:#cbd5e1; font-size:14px; line-height:1.65; margin-bottom:8px; }
.hz-meta { color:#94a3b8; font-size:13px; line-height:1.7; }
.hz-meta b { color:#e2e8f0; }
.panel { background:rgba(255,255,255,0.025); border:1px solid rgba(255,255,255,0.07); border-radius:16px; padding:20px 24px; margin-bottom:14px; }
.panel h4 { font-family:'Space Grotesk',sans-serif; color:#fff; margin:0 0 10px; font-size:16px; }
.panel li { color:#cbd5e1; font-size:14px; line-height:1.7; margin-bottom:4px; }
.how-section { margin:8px 0 32px; padding:32px 36px; background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06); border-radius:20px; }
.how-title { font-family:'Space Grotesk',sans-serif; font-size:20px; font-weight:600; color:#fff; margin-bottom:24px; }
.steps-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:24px; }
.step-item { text-align:center; }
.step-icon { width:48px; height:48px; background:rgba(220,38,38,0.1); border:1px solid rgba(220,38,38,0.2); border-radius:14px;
  display:flex; align-items:center; justify-content:center; font-size:20px; margin:0 auto 12px; }
.step-title { font-size:13px; font-weight:600; color:#e2e8f0; margin-bottom:6px; }
.step-desc { font-size:12px; color:#64748b; line-height:1.5; }
.sos { display:flex; justify-content:space-between; align-items:center; padding:12px 16px; border-radius:12px;
  background:rgba(220,38,38,0.07); border:1px solid rgba(220,38,38,0.2); margin-bottom:8px; }
.sos b { font-family:'Space Grotesk',sans-serif; font-size:22px; color:#f87171; }
.sos span { color:#cbd5e1; font-size:14px; }
.app-footer { text-align:center; padding:28px 24px 40px; border-top:1px solid rgba(255,255,255,0.05); color:#475569; font-size:13px; margin-top:24px; }
@media (max-width:800px){ .steps-grid{grid-template-columns:repeat(2,1fr);} [data-testid="stTabs"]{padding:0 14px;} }
</style>
""", unsafe_allow_html=True)

esc = lambda x: html.escape(str(x if x is not None else ""))

# ─────────────────────────────────────────────────────────────────────────────
# STATE + CLIENT
# ─────────────────────────────────────────────────────────────────────────────
st.session_state.setdefault("history", [])
st.session_state.setdefault("current", None)
st.session_state.setdefault("chat", [])
st.session_state.setdefault("query", PRESETS[1])


@st.cache_resource
def get_client():
    key = st.secrets["GROQ_API_KEY"]
    return Groq(api_key=key, http_client=httpx.Client())


# ─────────────────────────────────────────────────────────────────────────────
# AI LAYER
# ─────────────────────────────────────────────────────────────────────────────
def build_system_prompt(depth: str, lang: str) -> str:
    n = 3 if depth.startswith("Quick") else 8
    return f"""You are HazardLens, an expert safety inspector (OSHA, NDMA and fire-safety knowledge).
Analyze the image and the user's question. Respond with ONLY one valid JSON object, no markdown, no extra text:
{{
 "scene_summary": "1-2 sentences describing the scene",
 "primary_hazard": "short title of the main hazard (or 'No significant hazard')",
 "overall_risk": "Low|Medium|High|Critical",
 "risk_score": <integer 0-100>,
 "confidence": <integer 0-100>,
 "hazards": [ {{"name":"...", "category":"one of {CATEGORIES}", "severity":"Low|Medium|High|Critical",
   "description":"what it is and why it is dangerous (2-3 sentences)", "who_is_at_risk":"...",
   "immediate_action":"specific step to take right now"}} ],
 "preventive_measures": ["2-5 specific measures"],
 "who_to_contact": "who to call (fire dept, electricity board, municipal authority, 112 ...)",
 "answer_to_user_query": "direct, practical answer to the user's question"
}}
List at most {n} hazards, most severe first. Be specific to THIS image, no generic filler.
Write every text value in {lang}. Keep JSON keys and the words Low/Medium/High/Critical and category names in English.
If no hazard is visible use overall_risk "Low" and an empty hazards list."""


def is_missing_model(e: Exception) -> bool:
    s = str(e).lower()
    return "model_not_found" in s or "404" in s or "decommission" in s or "does not exist" in s


def chat_with_fallback(messages, preferred, json_mode, max_tokens):
    client = get_client()
    order = [preferred] + [m for m in MODELS.values() if m != preferred]
    errors = []
    for model in order:
        try:
            kwargs = dict(model=model, messages=messages, temperature=0.2, max_tokens=max_tokens)
            try:
                if json_mode:
                    r = client.chat.completions.create(response_format={"type": "json_object"}, **kwargs)
                else:
                    r = client.chat.completions.create(**kwargs)
            except Exception as e:
                if json_mode and not is_missing_model(e):
                    r = client.chat.completions.create(**kwargs)  # JSON mode unsupported -> plain retry
                else:
                    raise
            text = re.sub(r"<think>.*?</think>", "", r.choices[0].message.content or "", flags=re.S).strip()
            if not text:
                raise RuntimeError("empty response")
            return text, model
        except Exception as e:
            errors.append(f"{model}: {str(e)[:140]}")
    raise RuntimeError("All models failed -> " + " | ".join(errors))


def parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    m = re.search(r"\{.*\}", text, flags=re.S)
    return json.loads(m.group(0) if m else text)


def normalize(d: dict) -> dict:
    def sev(x):
        return {"low": "Low", "medium": "Medium", "high": "High", "critical": "Critical"}.get(str(x).strip().lower(), "Medium")

    hazards = []
    for h in d.get("hazards") or []:
        if isinstance(h, dict):
            cat = str(h.get("category", "Other")).strip().title()
            hazards.append({
                "name": h.get("name", "Unnamed hazard"), "category": cat if cat in CATEGORIES else "Other",
                "severity": sev(h.get("severity")), "description": h.get("description", ""),
                "who_is_at_risk": h.get("who_is_at_risk", "-"), "immediate_action": h.get("immediate_action", "-")})
    if d.get("overall_risk"):
        overall = sev(d["overall_risk"])
    elif hazards:
        overall = max((h["severity"] for h in hazards), key=SEV_ORDER.index)
    else:
        overall = "Low"
    try:
        score = max(0, min(100, int(float(d.get("risk_score")))))
    except Exception:
        score = SEV_SCORE[overall]
    try:
        conf = max(0, min(100, int(float(d.get("confidence")))))
    except Exception:
        conf = 80
    prev = d.get("preventive_measures") or []
    prev = [str(p) for p in prev] if isinstance(prev, list) else [str(prev)]
    return {"scene_summary": d.get("scene_summary", ""), "primary_hazard": d.get("primary_hazard", "-"),
            "overall_risk": overall, "risk_score": score, "confidence": conf, "hazards": hazards,
            "preventive_measures": prev, "who_to_contact": d.get("who_to_contact", "Local emergency services (112)."),
            "answer_to_user_query": d.get("answer_to_user_query", "")}


def prepare_image(file) -> bytes:
    img = ImageOps.exif_transpose(Image.open(file)).convert("RGB")
    img.thumbnail((1280, 1280))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return buf.getvalue()


def data_url(jpeg: bytes) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(jpeg).decode()


def run_analysis(jpeg, query, context, depth, lang, preferred):
    msgs = [{"role": "system", "content": build_system_prompt(depth, lang)},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": data_url(jpeg)}},
                {"type": "text", "text": f"Scene context: {context}\nUser question: {query}"}]}]
    text, used = chat_with_fallback(msgs, preferred, json_mode=True, max_tokens=3500)
    return normalize(parse_json(text)), used


def run_followup(cur, question):
    history = "\n".join(f"Q: {q}\nA: {a}" for q, a in st.session_state.chat[-4:])
    msgs = [{"role": "system", "content": "You are HazardLens, a safety assistant. Answer the follow-up concisely and practically, "
                                         "based on the image and the earlier analysis. Plain text, max 150 words. Reply in " + cur["lang"] + "."},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": data_url(cur["jpeg"])}},
                {"type": "text", "text": f"Earlier analysis (JSON): {json.dumps(cur['result'])[:3000]}\n\nPrevious follow-ups:\n{history}\n\nNew question: {question}"}]}]
    text, _ = chat_with_fallback(msgs, cur["model"], json_mode=False, max_tokens=1500)
    return text


# ─────────────────────────────────────────────────────────────────────────────
# REPORTS
# ─────────────────────────────────────────────────────────────────────────────
def build_markdown(cur) -> str:
    r = cur["result"]
    L = ["# HazardLens Safety Report", f"_Generated {cur['time']}_ | Model: `{cur['model']}` | Context: {cur['context']}", "",
         f"**Question:** {cur['query']}", "", "## Summary", r["scene_summary"], "",
         f"**Primary hazard:** {r['primary_hazard']}  ", f"**Overall risk:** {r['overall_risk']} ({r['risk_score']}/100)  ",
         f"**Confidence:** {r['confidence']}%", "", "## Hazards"]
    for h in r["hazards"]:
        L += [f"### {h['name']} [{h['severity']}] ({h['category']})", h["description"],
              f"- At risk: {h['who_is_at_risk']}", f"- Immediate action: {h['immediate_action']}", ""]
    L += ["## Preventive measures"] + [f"- {p}" for p in r["preventive_measures"]]
    L += ["", f"## Who to contact\n{r['who_to_contact']}", "", f"## Answer\n{r['answer_to_user_query']}", "",
          "_AI output is advisory. Call emergency services (112) in real danger._"]
    return "\n".join(L)


def build_pdf(cur) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Image as RLImage
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    def safe(t):  # reportlab core fonts are latin-1 only
        return html.escape(str(t or "")).encode("latin-1", "replace").decode("latin-1")

    r = cur["result"]
    ss = getSampleStyleSheet()
    H1 = ParagraphStyle("h1", parent=ss["Title"], textColor=colors.HexColor("#b91c1c"), fontSize=24)
    H2 = ParagraphStyle("h2", parent=ss["Heading2"], textColor=colors.HexColor("#111827"), spaceBefore=12)
    B = ParagraphStyle("b", parent=ss["BodyText"], fontSize=10, leading=14)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm)
    S = [Paragraph("HazardLens Safety Report", H1),
         Paragraph(safe(f"Generated {cur['time']}  |  Model: {cur['model']}  |  Context: {cur['context']}"), B), Spacer(1, 10)]
    try:
        im = Image.open(io.BytesIO(cur["jpeg"]))
        w = 9 * cm
        h = min(w * im.height / im.width, 8 * cm)
        S += [RLImage(io.BytesIO(cur["jpeg"]), width=h * im.width / im.height, height=h), Spacer(1, 10)]
    except Exception:
        pass
    col = colors.HexColor(SEV_COLOR[r["overall_risk"]])
    t = Table([["Overall risk", "Risk score", "Confidence", "Hazards"],
               [r["overall_risk"], f"{r['risk_score']}/100", f"{r['confidence']}%", str(len(r["hazards"]))]], colWidths=[4 * cm] * 4)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                           ("TEXTCOLOR", (0, 1), (0, 1), col), ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                           ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    S += [t, Paragraph("Question", H2), Paragraph(safe(cur["query"]), B), Paragraph("Summary", H2), Paragraph(safe(r["scene_summary"]), B),
          Paragraph("Primary hazard: " + safe(r["primary_hazard"]), B), Paragraph("Detected hazards", H2)]
    for h in r["hazards"]:
        c = SEV_COLOR[h["severity"]]
        S += [Paragraph(f'<font color="{c}"><b>[{h["severity"].upper()}]</b></font> <b>{safe(h["name"])}</b> ({h["category"]})', B),
              Paragraph(safe(h["description"]), B),
              Paragraph(f"<b>At risk:</b> {safe(h['who_is_at_risk'])}<br/><b>Immediate action:</b> {safe(h['immediate_action'])}", B), Spacer(1, 6)]
    S += [Paragraph("Preventive measures", H2)] + [Paragraph("&bull; " + safe(p), B) for p in r["preventive_measures"]]
    S += [Paragraph("Who to contact", H2), Paragraph(safe(r["who_to_contact"]), B), Paragraph("Answer", H2),
          Paragraph(safe(r["answer_to_user_query"]), B), Spacer(1, 14),
          Paragraph("<i>AI output is advisory. In real danger call emergency services (112 in India).</i>", B)]
    doc.build(S)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# RENDERING
# ─────────────────────────────────────────────────────────────────────────────
def tile(value, label, color="#ffffff", small=False):
    fs = "font-size:17px;" if small else ""
    return f'<div class="tile"><div class="tile-v" style="color:{color};{fs}">{esc(value)}</div><div class="tile-l">{esc(label)}</div></div>'


def render_result(cur):
    r = cur["result"]
    risk = r["overall_risk"]
    col = SEV_COLOR[risk]
    bad = risk != "Low"
    cls, tag_cls = ("result-danger", "tag-danger") if bad else ("result-safe", "tag-safe")
    tag = "⚠ Hazard Detected" if bad else "✓ Low Risk"
    st.markdown(
        f'<div class="{cls}"><div class="result-tag {tag_cls}">{tag}</div>'
        f'<div class="result-title">{esc(r["primary_hazard"])}</div>'
        f'<div class="result-text">{esc(r["scene_summary"])}</div>'
        f'<div class="gauge"><div class="gauge-fill" style="width:{r["risk_score"]}%;background:{col}"></div></div>'
        f'<div style="color:#64748b;font-size:11px;letter-spacing:1px;">RISK SCORE {r["risk_score"]}/100</div></div>',
        unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(tile(risk, "Overall risk", col), unsafe_allow_html=True)
    c2.markdown(tile(f'{r["risk_score"]}', "Risk score / 100"), unsafe_allow_html=True)
    c3.markdown(tile(len(r["hazards"]), "Hazards found"), unsafe_allow_html=True)
    c4.markdown(tile(f'{r["confidence"]}%', "AI confidence"), unsafe_allow_html=True)

    st.markdown('<div class="section-label" style="margin-top:22px">Direct answer</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="panel"><div class="result-text">{esc(r["answer_to_user_query"])}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-label">Detected hazards</div>', unsafe_allow_html=True)
    if not r["hazards"]:
        st.markdown('<div class="panel">✅ No significant hazards detected in this image.</div>', unsafe_allow_html=True)
    for h in r["hazards"]:
        c = SEV_COLOR[h["severity"]]
        st.markdown(
            f'<div class="hz" style="border-left:3px solid {c}"><div class="hz-top">'
            f'<span class="sev" style="background:{c}22;color:{c};border:1px solid {c}55">{h["severity"]}</span>'
            f'<span class="cat">{esc(h["category"])}</span><span class="hz-name">{esc(h["name"])}</span></div>'
            f'<div class="hz-desc">{esc(h["description"])}</div>'
            f'<div class="hz-meta"><b>👥 At risk:</b> {esc(h["who_is_at_risk"])}<br><b>✅ Do now:</b> {esc(h["immediate_action"])}</div></div>',
            unsafe_allow_html=True)

    a, b = st.columns(2)
    prev = "".join(f"<li>{esc(p)}</li>" for p in r["preventive_measures"])
    a.markdown(f'<div class="panel"><h4>🛡 Prevention measures</h4><ul style="margin:0;padding-left:18px">{prev}</ul></div>', unsafe_allow_html=True)
    b.markdown(f'<div class="panel"><h4>📞 Who to contact</h4><div class="result-text">{esc(r["who_to_contact"])}</div>'
               f'<div style="margin-top:10px;color:#f87171;font-size:13px">India emergency: 112 · Fire 101 · Ambulance 102/108</div></div>', unsafe_allow_html=True)

    # Downloads
    st.markdown('<div class="section-label" style="margin-top:8px">Export report</div>', unsafe_allow_html=True)
    d1, d2, d3 = st.columns(3)
    try:
        d1.download_button("📄 Download PDF report", build_pdf(cur), file_name="hazardlens_report.pdf", mime="application/pdf")
    except Exception as e:
        d1.caption(f"PDF unavailable: {e}")
    d2.download_button("📝 Download Markdown", build_markdown(cur), file_name="hazardlens_report.md")
    d3.download_button("🧾 Download JSON", json.dumps(r, indent=2, ensure_ascii=False), file_name="hazardlens_result.json")

    st.markdown('<div class="section-label" style="margin-top:18px">Quick share (copy & send)</div>', unsafe_allow_html=True)
    st.code(f"⚠ HazardLens alert: {r['primary_hazard']} | Risk: {risk} ({r['risk_score']}/100)\n"
            f"Action: {r['hazards'][0]['immediate_action'] if r['hazards'] else 'None needed'}\nEmergency: call 112", language=None)
    st.caption(f"Model used: {cur['model']} · {cur['time']}")

    # Follow-up chat
    st.markdown('<div class="section-label" style="margin-top:18px">Ask a follow-up about this image</div>', unsafe_allow_html=True)
    for q, ans in st.session_state.chat:
        with st.chat_message("user"):
            st.write(q)
        with st.chat_message("assistant"):
            st.write(ans)
    f1, f2 = st.columns([4, 1])
    fq = f1.text_input("Follow-up", key="followup_q", placeholder="e.g. Can I fix this myself or should I call a professional?",
                       label_visibility="collapsed")
    if f2.button("💬 Ask", key="followup_btn"):
        if fq.strip():
            with st.spinner("Thinking..."):
                try:
                    st.session_state.chat.append((fq.strip(), run_followup(cur, fq.strip())))
                    st.rerun()
                except Exception as e:
                    st.error(f"Follow-up failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────────────────────────────────────
n_done = len(st.session_state.history)
st.markdown(f"""
<div class="hero">
  <div class="hero-badge"><div class="dot"></div>AI-Powered Safety Analysis</div>
  <h1>Detect Danger<br><span>Instantly.</span></h1>
  <p class="hero-sub">Upload any scene. Get a risk score, hazard breakdown, action plan and a downloadable safety report in seconds.</p>
</div>
<div class="stats-row">
  <div class="stat-item"><div class="stat-num">27B</div><div class="stat-label">Vision Parameters</div></div><div class="stat-divider"></div>
  <div class="stat-item"><div class="stat-num">3</div><div class="stat-label">Auto-Fallback Models</div></div><div class="stat-divider"></div>
  <div class="stat-item"><div class="stat-num">{n_done}</div><div class="stat-label">Analyses This Session</div></div><div class="stat-divider"></div>
  <div class="stat-item"><div class="stat-num">Free</div><div class="stat-label">Groq Powered</div></div>
</div>
""", unsafe_allow_html=True)

tab_an, tab_hist, tab_sos, tab_about = st.tabs(["🔍 Analyze", "📊 History & Analytics", "🚨 Emergency Guide", "ℹ️ About"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB: ANALYZE
# ─────────────────────────────────────────────────────────────────────────────
with tab_an:
    try:
        st.secrets["GROQ_API_KEY"]
    except Exception:
        st.error("GROQ_API_KEY missing. Add it in Streamlit Cloud → Manage app → Settings → Secrets:  GROQ_API_KEY = \"gsk_...\"")
        st.stop()

    def apply_preset():
        p = st.session_state.get("preset")
        if p and p != PRESETS[0]:
            st.session_state.query = p

    with st.container(key="maincard"):
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.markdown('<div class="section-label">Image</div>', unsafe_allow_html=True)
            src = st.radio("Source", ["Upload", "Camera"], horizontal=True, label_visibility="collapsed")
            if src == "Upload":
                file = st.file_uploader("Drop image", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")
            else:
                file = st.camera_input("Take photo", label_visibility="collapsed")
            if file:
                st.image(file)
        with col2:
            st.markdown('<div class="section-label">Your Query</div>', unsafe_allow_html=True)
            st.selectbox("Presets", PRESETS, key="preset", on_change=apply_preset, label_visibility="collapsed")
            query = st.text_area("Query", key="query", height=110, label_visibility="collapsed")
            s1, s2 = st.columns(2)
            model_label = s1.selectbox("Model", list(MODELS.keys()))
            context = s2.selectbox("Scene context", CONTEXTS)
            s3, s4 = st.columns(2)
            depth = s3.selectbox("Analysis depth", DEPTHS)
            lang = s4.selectbox("Response language", LANGUAGES)
            go = st.button("⚡ Analyze for Hazards", key="analyze_btn")

    if go:
        if not file:
            st.error("Please upload or capture an image first.")
        elif not query.strip():
            st.error("Please enter a question.")
        else:
            with st.spinner("🔍 Analyzing image — please wait..."):
                try:
                    jpeg = prepare_image(file)
                    result, used = run_analysis(jpeg, query.strip(), context, depth, lang, MODELS[model_label])
                    now = datetime.now().strftime("%d %b %Y, %H:%M")
                    st.session_state.current = {"result": result, "jpeg": jpeg, "query": query.strip(), "context": context,
                                                "model": used, "time": now, "lang": lang}
                    st.session_state.chat = []
                    top = max(result["hazards"], key=lambda h: SEV_ORDER.index(h["severity"]))["category"] if result["hazards"] else "None"
                    st.session_state.history.append({"time": now, "primary_hazard": result["primary_hazard"], "risk": result["overall_risk"],
                                                     "score": result["risk_score"], "hazards": len(result["hazards"]), "category": top,
                                                     "context": context, "model": used})
                    st.success("✅ Analysis completed successfully")
                except Exception as e:
                    st.error(f"Analysis failed: {e}")

    if st.session_state.current:
        render_result(st.session_state.current)

    st.markdown("""
    <div class="how-section"><div class="how-title">How it works</div><div class="steps-grid">
      <div class="step-item"><div class="step-icon">🖼️</div><div class="step-title">Upload Image</div><div class="step-desc">JPG, PNG or WEBP — or use your camera</div></div>
      <div class="step-item"><div class="step-icon">💬</div><div class="step-title">Ask a Question</div><div class="step-desc">Natural language query in English, Hindi or Hinglish</div></div>
      <div class="step-item"><div class="step-icon">🧠</div><div class="step-title">AI Inference</div><div class="step-desc">Qwen 3.x vision model reasons about the scene</div></div>
      <div class="step-item"><div class="step-icon">⚡</div><div class="step-title">Hazard Report</div><div class="step-desc">Risk score, actions and a PDF report</div></div>
    </div></div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB: HISTORY
# ─────────────────────────────────────────────────────────────────────────────
with tab_hist:
    if not st.session_state.history:
        st.info("No analyses yet. Run one in the Analyze tab.")
    else:
        df = pd.DataFrame(st.session_state.history)
        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(tile(len(df), "Total analyses"), unsafe_allow_html=True)
        m2.markdown(tile(f"{df['score'].mean():.0f}", "Avg risk score"), unsafe_allow_html=True)
        m3.markdown(tile(int(df["risk"].isin(["High", "Critical"]).sum()), "High / Critical", "#ef4444"), unsafe_allow_html=True)
        m4.markdown(tile(int(df["hazards"].sum()), "Hazards found"), unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        with g1:
            st.markdown('<div class="section-label">Risk level distribution</div>', unsafe_allow_html=True)
            st.bar_chart(df["risk"].value_counts().reindex(SEV_ORDER, fill_value=0))
        with g2:
            st.markdown('<div class="section-label">Hazard categories</div>', unsafe_allow_html=True)
            st.bar_chart(df[df["category"] != "None"]["category"].value_counts())
        st.markdown('<div class="section-label">Risk score trend</div>', unsafe_allow_html=True)
        st.line_chart(df["score"])
        st.dataframe(df)
        h1, h2 = st.columns(2)
        h1.download_button("⬇️ Export history (CSV)", df.to_csv(index=False), file_name="hazardlens_history.csv")
        if h2.button("🗑 Clear history", key="clear_hist"):
            st.session_state.history = []
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TAB: EMERGENCY GUIDE
# ─────────────────────────────────────────────────────────────────────────────
with tab_sos:
    a, b = st.columns(2, gap="large")
    with a:
        st.markdown('<div class="section-label">India emergency numbers</div>', unsafe_allow_html=True)
        for num, lbl in [("112", "National emergency (all services)"), ("100", "Police"), ("101", "Fire brigade"),
                         ("102 / 108", "Ambulance"), ("1078", "NDMA disaster management")]:
            st.markdown(f'<div class="sos"><span>{lbl}</span><b>{num}</b></div>', unsafe_allow_html=True)
        st.caption("Verify numbers for your state/city. Utilities (electricity, gas, water) have separate local helplines.")
    with b:
        st.markdown('<div class="section-label">First-response checklist</div>', unsafe_allow_html=True)
        st.markdown("""
<div class="panel"><ul style="margin:0;padding-left:18px">
<li><b>Electrical:</b> Do not touch. Switch off at the main breaker if safe. Never use water.</li>
<li><b>Fire:</b> Evacuate first, then call 101. Stay low under smoke. Never use lifts.</li>
<li><b>Gas leak:</b> No flames or switches. Open windows, leave, call from outside.</li>
<li><b>Water / pipe burst:</b> Close the main valve, switch off nearby electricity, move valuables up.</li>
<li><b>Structural damage:</b> Keep people away, barricade the area, call the municipal authority.</li>
<li><b>Chemical spill:</b> Move upwind, avoid contact, cover nose and mouth, call 112.</li>
</ul></div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB: ABOUT
# ─────────────────────────────────────────────────────────────────────────────
with tab_about:
    st.markdown("""
<div class="panel"><h4>About HazardLens</h4>
<div class="result-text">HazardLens is an AI-powered visual safety inspector. A multimodal vision-language model examines an image,
identifies hazards, scores the overall risk and generates an actionable safety report.</div></div>
<div class="panel"><h4>Key features</h4><ul style="margin:0;padding-left:18px">
<li>Structured analysis: risk score, confidence, severity-rated hazards with categories</li>
<li>Scene-context aware prompts (road, construction, industrial, home, fire, flood...)</li>
<li>Multilingual output: English, Hindi, Hinglish</li>
<li>Follow-up Q&amp;A on the same image</li>
<li>Exports: PDF, Markdown, JSON, CSV history</li>
<li>Session analytics dashboard and emergency guide</li>
<li>Automatic model fallback so retired models never break the app</li></ul></div>
<div class="panel"><h4>Tech stack</h4><div class="result-text">Python · Streamlit · Groq API (Qwen 3.x multimodal) · Pillow · Pandas · ReportLab · HTTPX</div></div>
<div class="panel"><h4>Disclaimer</h4><div class="result-text">AI output is advisory and may be wrong. It is not a substitute for a qualified
safety professional. In real danger, call emergency services immediately (112 in India).</div></div>
""", unsafe_allow_html=True)

st.markdown('<div class="app-footer">⚡ HazardLens AI · Built with Streamlit &amp; Groq · Final Year Project</div>', unsafe_allow_html=True)
