"""Application pages."""
import json
import os
from datetime import datetime

import pandas as pd
import streamlit as st

from . import ai, imaging, report, risk, state
from .config import (DEPTH, EMERGENCY, LANGUAGES, MODELS, PRESETS, SITE_TYPES, STATUSES, TZ, VERSION)
from .risk import BAND_COLOR, BANDS
from .ui import components as c

ACCENT = "#f2a33a"


# ───────────────────────── helpers ─────────────────────────
def _api_key():
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return os.environ.get("GROQ_API_KEY")


@st.cache_resource(show_spinner=False)
def _client(key: str):
    return ai.make_client(key)


def _settings():
    engine = st.session_state.get("engine", list(MODELS)[0])
    lang = st.session_state.get("lang", "English")
    depth = st.session_state.get("depth", list(DEPTH)[0])
    return MODELS[engine], lang, DEPTH[depth]


# ───────────────────────── result view ─────────────────────────
def result_view(rec: dict):
    r = rec["result"]
    band = r["overall_band"]
    col = BAND_COLOR[band]
    st.markdown("<br>", unsafe_allow_html=True)
    c.render(f'<div class="hl-label">Assessment · {c.esc(rec["id"])}</div>')

    left, right = st.columns([1.25, 1], gap="large")
    with left:
        st.image(rec["annotated"])
        c.render('<div class="legend">' + "".join(f'<span style="--c:{BAND_COLOR[b]}">{b}</span>' for b in BANDS)
                 + '<span style="--c:#8a93a5">Markers = approximate hazard location (3×3 grid)</span></div>')
    with right:
        c.render(f'<div class="hl-card" style="text-align:center;padding-bottom:34px">{c.gauge(r["risk_index"], col, "Risk index / 100")}</div>')
        k1, k2 = st.columns(2)
        k1.markdown(c.flat(c.kpi("Overall rating", band, f"Top score {r['overall_score']}/25", col)), unsafe_allow_html=True)
        k2.markdown(c.flat(c.kpi("Hazards", len(r["hazards"]), f"Confidence {r['confidence']}%")), unsafe_allow_html=True)

    c.render(f'<div class="hl-panel" style="margin-top:18px"><h4>Executive summary</h4><p>{c.esc(r["summary"])}</p>'
             f'<h4 style="margin-top:14px">Answer to inspection question</h4><p>{c.esc(r["answer"])}</p></div>')

    # export
    if "pdf" not in rec:
        try:
            rec["pdf"] = report.build_pdf(rec)
        except Exception as e:  # keep the app usable if PDF fails
            rec["pdf"] = None
            rec["pdf_error"] = str(e)
    e1, e2, e3 = st.columns(3)
    if rec.get("pdf"):
        e1.download_button("Download PDF report", rec["pdf"], file_name=f"{rec['id']}.pdf", mime="application/pdf", key=f"pdf_{rec['id']}")
    else:
        e1.caption(f"PDF unavailable: {rec.get('pdf_error', '')}")
    e2.download_button("Download Markdown", report.build_markdown(rec), file_name=f"{rec['id']}.md", key=f"md_{rec['id']}")
    e3.download_button("Download JSON", json.dumps(r, indent=2, ensure_ascii=False), file_name=f"{rec['id']}.json", key=f"js_{rec['id']}")

    t1, t2, t3, t4 = st.tabs(["Risk register", "Risk matrix", "Action plan", "Prevention & references"])
    with t1:
        if not r["hazards"]:
            c.panel("No significant hazards", "No hazards were identified in this image.")
        for h in r["hazards"]:
            c.render(c.hazard_card(h))
        if r["observations"]:
            c.panel("Positive observations", c.bullet_list(r["observations"]), raw=True)
    with t2:
        a, b = st.columns([1.5, 1], gap="large")
        with a:
            c.render(f'<div class="hl-card">{c.matrix(hazards=r["hazards"])}</div>')
        with b:
            c.panel("How to read this", "Each hazard is plotted by likelihood and severity. Score = L × S. "
                    "Bands: 1–4 Low, 5–9 Medium, 10–14 High, 15–25 Critical. Ratings are produced by the vision model; "
                    "scores and bands are computed deterministically by the risk engine.")
    with t3:
        if r["actions"]:
            rows = [[f'<span class="mono">{c.esc(a["priority"])}</span> {c.esc(risk.PRIORITIES[a["priority"]])}',
                     c.esc(a["action"]), c.esc(a["owner"]), c.esc(a["timeframe"])] for a in r["actions"]]
            c.render(f'<div class="hl-card">{c.table(["Priority", "Action", "Owner", "Timeframe"], rows)}</div>')
        else:
            c.panel("No actions required", "No corrective actions were generated.")
        c.panel("Notify", r["contact"])
    with t4:
        p1, p2 = st.columns(2, gap="large")
        with p1:
            c.panel("Preventive measures", c.bullet_list(r["prevention"]), raw=True)
        with p2:
            c.panel("Indicative references", c.bullet_list(r["references"]) +
                    '<p style="font-size:12px;color:#8a93a5;margin-top:8px">Generated suggestions - verify against the current standard before citing.</p>', raw=True)

    # follow-up
    c.label("Follow-up questions")
    for q, a in rec["chat"]:
        with st.chat_message("user"):
            st.write(q)
        with st.chat_message("assistant"):
            st.write(a)
    with st.form(f"fu_{rec['id']}", clear_on_submit=True):
        f1, f2 = st.columns([5, 1])
        q = f1.text_input("Follow-up", placeholder="e.g. Can this be repaired without shutting down the line?", label_visibility="collapsed")
        sent = f2.form_submit_button("Ask")
    if sent and q.strip():
        model, lang, _ = _settings()
        with st.spinner("Analysing..."):
            try:
                rec["chat"].append((q.strip(), ai.follow_up(_client(_api_key()), rec["jpeg"], json.dumps(r), rec["chat"], q.strip(),
                                                           LANGUAGES[lang], model)))
                st.rerun()
            except Exception as e:
                st.error(f"Follow-up failed: {e}")


# ───────────────────────── pages ─────────────────────────
def dashboard():
    state.init()
    c.page_header("Risk dashboard", "Portfolio view of every inspection completed in this session.", "Dashboard",
                  chips=[(f"v{VERSION}", "#8a93a5"), ("5×5 risk matrix", ACCENT), ("Session workspace", "#8a93a5")])
    recs = st.session_state.records
    if not recs:
        a, b = st.columns([1.2, 1], gap="large")
        with a:
            c.render('<div class="hl-panel"><h4>Get started</h4>'
                     '<div class="step"><div class="n">1</div><p><b>Open New inspection</b> from the sidebar and add a photo of the site or asset.</p></div>'
                     '<div class="step"><div class="n">2</div><p><b>Record context</b> - site, location, inspector - and ask a specific question.</p></div>'
                     '<div class="step"><div class="n">3</div><p><b>Run the assessment</b> to get a scored risk register, action plan and a PDF report.</p></div>'
                     '<div class="step"><div class="n">4</div><p><b>Track closure</b> from the Inspection register and watch this dashboard fill up.</p></div></div>')
        with b:
            c.render(f'<div class="hl-card">{c.matrix(counts={})}</div>')
        return

    idx = [r["result"]["risk_index"] for r in recs]
    open_hi = sum(1 for r in recs if r["result"]["overall_band"] in ("High", "Critical") and r["status"] != "Closed")
    closed = sum(1 for r in recs if r["status"] == "Closed")
    n_haz = sum(len(r["result"]["hazards"]) for r in recs)
    k = st.columns(4)
    k[0].markdown(c.flat(c.kpi("Inspections", len(recs), f"{n_haz} hazards identified")), unsafe_allow_html=True)
    k[1].markdown(c.flat(c.kpi("Average risk index", round(sum(idx) / len(idx)), "out of 100", ACCENT)), unsafe_allow_html=True)
    k[2].markdown(c.flat(c.kpi("Open high / critical", open_hi, "needs attention", BAND_COLOR["Critical"] if open_hi else BAND_COLOR["Low"])), unsafe_allow_html=True)
    k[3].markdown(c.flat(c.kpi("Closure rate", f"{round(closed / len(recs) * 100)}%", f"{closed} of {len(recs)} closed", BAND_COLOR["Low"])), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    a, b = st.columns(2, gap="large")
    with a:
        dist = [(bd, sum(1 for r in recs if r["result"]["overall_band"] == bd), BAND_COLOR[bd]) for bd in BANDS]
        c.panel("Inspections by overall rating", c.bars(dist), raw=True)
    with b:
        cats = {}
        for r in recs:
            for h in r["result"]["hazards"]:
                cats[h["category"]] = cats.get(h["category"], 0) + 1
        rows = [(k_, v, ACCENT) for k_, v in sorted(cats.items(), key=lambda x: -x[1])[:6]] or [("No hazards", 0, ACCENT)]
        c.panel("Hazards by category", c.bars(rows), raw=True)

    a, b = st.columns([1.3, 1], gap="large")
    with a:
        recent = [[f'<span class="mono">{c.esc(r["id"])}</span>', c.esc(r["site"] or "-"), c.esc(r["result"]["primary_hazard"]),
                   c.band_chip(r["result"]["overall_band"]), c.esc(r["status"])] for r in reversed(recs[-6:])]
        c.label("Recent inspections")
        c.render(f'<div class="hl-card">{c.table(["ID", "Site", "Primary hazard", "Rating", "Status"], recent)}</div>')
    with b:
        counts = {}
        for r in recs:
            for key, v in risk.matrix_counts(r["result"]["hazards"]).items():
                counts[key] = counts.get(key, 0) + v
        c.label("Portfolio risk matrix")
        c.render(f'<div class="hl-card">{c.matrix(counts=counts)}</div>')

    if len(recs) > 1:
        c.label("Risk index trend")
        st.line_chart(pd.DataFrame({"Risk index": idx}, index=[r["id"] for r in recs]), color=ACCENT, height=220)


def inspection():
    state.init()
    c.page_header("New inspection", "Capture evidence, record site details and generate a quantified risk assessment.", "Inspections",
                  chips=[("5×5 risk matrix", ACCENT), ("Hazard locator", "#8a93a5"), ("PDF report", "#8a93a5")])
    key = _api_key()
    if not key:
        st.error("GROQ_API_KEY is not configured. Add it in Streamlit Cloud → Manage app → Settings → Secrets:  GROQ_API_KEY = \"gsk_...\"")
        return

    def apply_preset():
        p = st.session_state.get("preset")
        if p and p != PRESETS[0]:
            st.session_state.query = p

    with st.container(key="formcard"):
        left, right = st.columns([1.05, 1], gap="large")
        with left:
            c.label("Evidence")
            src = st.radio("Source", ["Upload image", "Use camera"], horizontal=True, label_visibility="collapsed")
            if src == "Upload image":
                file = st.file_uploader("Evidence", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")
            else:
                file = st.camera_input("Camera", label_visibility="collapsed")
            if file:
                st.image(file)
        with right:
            c.label("Inspection details")
            a, b = st.columns(2)
            site = a.text_input("Site / asset", placeholder="e.g. Plant 2 – cooling line")
            location = b.text_input("Location", placeholder="e.g. Sector 62, Noida")
            inspector = a.text_input("Inspector", placeholder="Name")
            site_type = b.selectbox("Scene type", SITE_TYPES)
            c.label("Inspection question")
            st.selectbox("Presets", PRESETS, key="preset", on_change=apply_preset, label_visibility="collapsed")
            question = st.text_area("Question", key="query", height=96, label_visibility="collapsed")
            run = st.button("Run assessment", type="primary", key="run_btn")

    if run:
        if not file:
            st.warning("Add an image first.")
        elif not question.strip():
            st.warning("Enter an inspection question.")
        else:
            model, lang, max_h = _settings()
            with st.status("Running assessment", expanded=True) as status:
                try:
                    st.write("Preparing evidence image")
                    jpeg = imaging.prepare_image(file)
                    st.write("Running vision analysis")
                    raw, used = ai.analyze(_client(key), jpeg, question.strip(), site_type, max_h, LANGUAGES[lang], model)
                    st.write("Scoring risk matrix")
                    result = risk.normalize(raw)
                    st.write("Annotating hazard locations")
                    annotated = imaging.annotate(jpeg, result["hazards"])
                except Exception as e:
                    status.update(label="Assessment failed", state="error")
                    st.error(str(e))
                else:
                    rec = {"id": state.next_id(), "time": datetime.now(TZ).strftime("%d %b %Y, %H:%M IST"), "site": site.strip(),
                           "location": location.strip(), "inspector": inspector.strip(), "site_type": site_type,
                           "question": question.strip(), "model": used, "status": "Open", "result": result,
                           "jpeg": jpeg, "annotated": annotated, "chat": []}
                    state.add(rec)
                    status.update(label=f"Assessment complete · {rec['id']}", state="complete", expanded=False)

    rec = state.current()
    if rec:
        result_view(rec)


def register():
    state.init()
    c.page_header("Inspection register", "Search, review and close out inspections. Status changes apply to this session.", "Register",
                  chips=[("Session records", "#8a93a5")])
    recs = st.session_state.records
    if not recs:
        c.panel("Register is empty", "Completed inspections will appear here.")
        return
    f1, f2 = st.columns([2, 1])
    q = f1.text_input("Search", placeholder="Search by ID, site or hazard", label_visibility="collapsed")
    bands = f2.multiselect("Rating", BANDS, default=BANDS, label_visibility="collapsed")
    rows = [{"ID": r["id"], "Date": r["time"], "Site": r["site"] or "-", "Primary hazard": r["result"]["primary_hazard"],
             "Rating": r["result"]["overall_band"], "Risk index": r["result"]["risk_index"],
             "Hazards": len(r["result"]["hazards"]), "Status": r["status"]} for r in recs]
    df = pd.DataFrame(rows)
    df = df[df["Rating"].isin(bands)]
    if q.strip():
        m = df.apply(lambda row: q.lower() in " ".join(map(str, row.values)).lower(), axis=1)
        df = df[m]
    edited = st.data_editor(
        df, hide_index=True, key="reg_editor", disabled=[x for x in df.columns if x != "Status"],
        column_config={"Status": st.column_config.SelectboxColumn("Status", options=STATUSES, required=True),
                       "Risk index": st.column_config.ProgressColumn("Risk index", min_value=0, max_value=100, format="%d")})
    for _, row in edited.iterrows():
        target = state.get(row["ID"])
        if target:
            target["status"] = row["Status"]

    d1, d2 = st.columns([1, 3])
    d1.download_button("Export register (CSV)", edited.to_csv(index=False), file_name="hazardlens_register.csv")
    if not df.empty:
        c.label("Inspection detail")
        pick = st.selectbox("Open inspection", df["ID"].tolist(), label_visibility="collapsed")
        rec = state.get(pick)
        if rec:
            result_view(rec)


def methodology():
    state.init()
    c.page_header("Methodology & safety", "How scores are produced, what the system can and cannot do, and who to call in an emergency.",
                  "Methodology", chips=[("Documentation", "#8a93a5")])
    a, b = st.columns([1.3, 1], gap="large")
    with a:
        c.label("Risk matrix")
        c.render(f'<div class="hl-card">{c.matrix(counts={})}</div>')
        c.panel("Scoring method",
                "<p>For every hazard the vision model proposes <b>likelihood (1–5)</b> and <b>severity (1–5)</b>. "
                "The risk engine computes <b>score = L × S</b> and assigns a band: 1–4 Low, 5–9 Medium, 10–14 High, 15–25 Critical. "
                "The <b>risk index (0–100)</b> is driven by the highest score with a small uplift for the number of hazards. "
                "Scores are never taken from the model's free text, so the same ratings always give the same result.</p>", raw=True)
        c.panel("Pipeline", c.bullet_list([
            "Image preparation: EXIF correction, RGB conversion, resize to 1280 px, JPEG re-encode",
            "Vision inference: Groq-hosted multimodal model with a strict JSON schema, with automatic fallback to alternative models",
            "Validation and normalisation: type clamping, enum matching, derived action plan if missing",
            "Risk engine: deterministic L × S scoring, banding and index",
            "Evidence annotation: numbered hazard markers on a 3×3 locator grid",
            "Reporting: PDF, Markdown, JSON and CSV exports"]), raw=True)
        c.panel("Limitations", c.bullet_list([
            "Assessments are advisory; the model can miss hazards or misjudge severity from a single photo",
            "Hazard locations are approximate (3×3 grid), not pixel-accurate detection",
            "Referenced standards are suggestions and must be verified before citing",
            "Records are kept only in your browser session and are cleared when it ends"]), raw=True)
    with b:
        c.label("Emergency numbers (India)")
        c.render("".join(f'<div class="sos"><span>{c.esc(l)}</span><b>{c.esc(n)}</b></div>' for n, l in EMERGENCY))
        st.caption("Verify numbers for your state. Electricity, gas and water utilities have separate local helplines.")
        c.panel("First response", c.bullet_list([
            "Electrical: do not touch; isolate at the main breaker only if safe; never use water",
            "Fire: evacuate first, call 101, stay low, never use lifts",
            "Gas leak: no flames or switches; ventilate, leave, call from outside",
            "Water / pipe burst: close the main valve and switch off nearby electricity",
            "Structural damage: keep people away, barricade, notify the municipal authority",
            "Chemical spill: move upwind, avoid contact, call 112"]), raw=True)
        c.panel("Technology", "Python · Streamlit · Groq (Qwen 3.x multimodal) · Pillow · Pandas · ReportLab · HTTPX · pytest")
