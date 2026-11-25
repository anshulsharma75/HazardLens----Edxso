"""Inspection report generation (PDF + Markdown)."""
import html
import io

from .risk import BAND_COLOR, LIKELIHOOD, PRIORITIES, SEVERITY, band_for


def _safe(text) -> str:
    """Escape for reportlab Paragraph; core PDF fonts are latin-1 only."""
    return html.escape(str(text or "")).encode("latin-1", "replace").decode("latin-1")


def build_markdown(rec: dict) -> str:
    r = rec["result"]
    L = [f"# Inspection Report {rec['id']}", "",
         f"- **Site / asset:** {rec['site'] or '-'}", f"- **Location:** {rec['location'] or '-'}",
         f"- **Inspector:** {rec['inspector'] or '-'}", f"- **Date:** {rec['time']}",
         f"- **Scene type:** {rec['site_type']}", f"- **Engine:** {rec['model']}", f"- **Status:** {rec['status']}", "",
         f"**Question:** {rec['question']}", "", "## Executive summary", r["summary"], "",
         f"**Overall rating:** {r['overall_band']} (highest score {r['overall_score']}/25) · "
         f"**Risk index:** {r['risk_index']}/100 · **Confidence:** {r['confidence']}%", "",
         "## Risk register", "", "| Ref | Hazard | Category | Zone | L | S | Score | Rating |", "|---|---|---|---|---|---|---|---|"]
    for h in r["hazards"]:
        L.append(f"| {h['ref']} | {h['name']} | {h['category']} | {h['zone']} | {h['likelihood']} | {h['severity']} | {h['score']} | {h['band']} |")
    L += ["", "## Hazard details"]
    for h in r["hazards"]:
        L += [f"### {h['ref']} - {h['name']} ({h['band']})", h["description"], f"- Consequence: {h['consequence'] or '-'}",
              f"- At risk: {h['who_is_at_risk']}", f"- Immediate action: {h['immediate_action']}", ""]
    L += ["## Corrective action plan", "", "| Priority | Action | Owner | Timeframe |", "|---|---|---|---|"]
    for a in r["actions"]:
        L.append(f"| {a['priority']} | {a['action']} | {a['owner']} | {a['timeframe']} |")
    L += ["", "## Preventive measures"] + [f"- {p}" for p in r["prevention"]]
    if r["references"]:
        L += ["", "## Indicative references (verify before citing)"] + [f"- {x}" for x in r["references"]]
    L += ["", f"## Notify\n{r['contact']}", "", f"## Answer to inspection question\n{r['answer']}", "",
          "_Automated assessment - advisory only. Verify on site with a qualified safety professional. Emergency: 112._"]
    return "\n".join(L)


def build_pdf(rec: dict) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Image as RLImage
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    r = rec["result"]
    ss = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=ss["BodyText"], fontSize=9, leading=12.5, textColor=colors.HexColor("#1f2933"))
    small = ParagraphStyle("small", parent=body, fontSize=8, leading=10.5)
    cellw = ParagraphStyle("cellw", parent=small, textColor=colors.white, fontName="Helvetica-Bold", alignment=1)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=12.5, spaceBefore=14, spaceAfter=6,
                        textColor=colors.HexColor("#111827"))
    title = ParagraphStyle("title", parent=ss["Title"], fontSize=20, alignment=0, textColor=colors.HexColor("#111827"))
    P = lambda t, s=body: Paragraph(_safe(t), s)
    dark = colors.HexColor("#111827")
    line = colors.HexColor("#d5dae1")

    def decorate(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#0f1319"))
        canvas.rect(0, A4[1] - 1.5 * cm, A4[0], 1.5 * cm, stroke=0, fill=1)
        canvas.setFillColor(colors.HexColor("#f2a33a"))
        canvas.rect(0, A4[1] - 1.5 * cm, 0.35 * cm, 1.5 * cm, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(1.4 * cm, A4[1] - 0.95 * cm, "HAZARDLENS  |  Visual Risk Assessment")
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 0.95 * cm, rec["id"])
        canvas.setFillColor(colors.HexColor("#6b7280"))
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(2 * cm, 1.1 * cm, "Automated assessment - advisory only. Verify on site with a qualified safety professional.")
        canvas.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"Page {doc.page}")
        canvas.restoreState()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2.4 * cm, bottomMargin=1.8 * cm,
                            title=f"Inspection Report {rec['id']}", author="HazardLens")
    S = [Paragraph("Inspection Report", title), Spacer(1, 4)]

    meta = [[P("Site / asset", small), P(rec["site"] or "-"), P("Date", small), P(rec["time"])],
            [P("Location", small), P(rec["location"] or "-"), P("Scene type", small), P(rec["site_type"])],
            [P("Inspector", small), P(rec["inspector"] or "-"), P("Status", small), P(rec["status"])]]
    t = Table(meta, colWidths=[2.6 * cm, 6 * cm, 2.6 * cm, 5.8 * cm])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, line), ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
                           ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f3f4f6")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    S += [t, Spacer(1, 10)]

    bc = colors.HexColor(BAND_COLOR[r["overall_band"]])
    kp = Table([[P("OVERALL RATING", small), P("RISK INDEX", small), P("TOP SCORE", small), P("HAZARDS", small), P("CONFIDENCE", small)],
                [Paragraph(f"<b>{r['overall_band']}</b>", ParagraphStyle("k", parent=body, fontSize=14, textColor=bc)),
                 Paragraph(f"<b>{r['risk_index']}/100</b>", ParagraphStyle("k2", parent=body, fontSize=14)),
                 Paragraph(f"<b>{r['overall_score']}/25</b>", ParagraphStyle("k3", parent=body, fontSize=14)),
                 Paragraph(f"<b>{len(r['hazards'])}</b>", ParagraphStyle("k4", parent=body, fontSize=14)),
                 Paragraph(f"<b>{r['confidence']}%</b>", ParagraphStyle("k5", parent=body, fontSize=14))]],
               colWidths=[3.4 * cm] * 5)
    kp.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, line), ("LINEBEFORE", (1, 0), (-1, -1), 0.4, line),
                            ("LINEABOVE", (0, 0), (-1, 0), 2.5, bc), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    S += [kp, Paragraph("Inspection question", h2), P(rec["question"]), Paragraph("Executive summary", h2), P(r["summary"])]

    try:
        from PIL import Image
        img_bytes = rec.get("annotated") or rec["jpeg"]
        im = Image.open(io.BytesIO(img_bytes))
        h = min(9 * cm * im.height / im.width, 9 * cm)
        S += [Spacer(1, 8), RLImage(io.BytesIO(img_bytes), width=h * im.width / im.height, height=h),
              P("Figure 1 - Evidence photo with approximate hazard locations (numbered markers, 3x3 locator grid).", small)]
    except Exception:
        pass

    # Risk register
    S.append(Paragraph("Risk register", h2))
    rows = [[P(x, small) for x in ("Ref", "Hazard", "Category", "Zone", "L", "S", "Score", "Rating")]]
    style = [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")), ("GRID", (0, 0), (-1, -1), 0.4, line),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]
    for i, hz in enumerate(r["hazards"], 1):
        rows.append([P(hz["ref"], small), P(hz["name"], small), P(hz["category"], small), P(hz["zone"], small),
                     P(hz["likelihood"], small), P(hz["severity"], small), P(hz["score"], small),
                     Paragraph(_safe(hz["band"]), cellw)])
        style.append(("BACKGROUND", (7, i), (7, i), colors.HexColor(BAND_COLOR[hz["band"]])))
    if len(rows) == 1:
        rows.append([P("-", small)] * 8)
    t = Table(rows, colWidths=[1.1 * cm, 5 * cm, 2.3 * cm, 2.5 * cm, 0.9 * cm, 0.9 * cm, 1.4 * cm, 2.9 * cm], repeatRows=1)
    t.setStyle(TableStyle(style))
    S.append(t)

    # Matrix
    S.append(Paragraph("Risk matrix (likelihood x severity)", h2))
    grid = [[P("L \\ S", small)] + [P(f"{s} {SEVERITY[s]}", small) for s in range(1, 6)]]
    mstyle = [("GRID", (0, 0), (-1, -1), 0.5, colors.white), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (1, 1), (-1, -1), "CENTER")]
    for ri, l in enumerate(range(5, 0, -1), 1):
        row = [P(f"{l} {LIKELIHOOD[l]}", small)]
        for ci, s in enumerate(range(1, 6), 1):
            refs = ", ".join(h["ref"] for h in r["hazards"] if h["likelihood"] == l and h["severity"] == s)
            row.append(Paragraph(_safe(f"{l * s}" + (f"<br/>{refs}" if refs else "")).replace("&lt;br/&gt;", "<br/>"), cellw))
            mstyle.append(("BACKGROUND", (ci, ri), (ci, ri), colors.HexColor(BAND_COLOR[band_for(l * s)])))
        grid.append(row)
    t = Table(grid, colWidths=[3 * cm] + [2.7 * cm] * 5, rowHeights=[0.8 * cm] + [0.95 * cm] * 5)
    t.setStyle(TableStyle(mstyle))
    S.append(t)

    # Hazard details
    S.append(Paragraph("Hazard details", h2))
    for hz in r["hazards"]:
        c = BAND_COLOR[hz["band"]]
        S += [Paragraph(f'<font color="{c}"><b>{hz["ref"]} &middot; {_safe(hz["band"]).upper()}</b></font> &nbsp; <b>{_safe(hz["name"])}</b>', body),
              P(hz["description"]),
              Paragraph(f"<b>Consequence:</b> {_safe(hz['consequence'] or '-')}<br/><b>At risk:</b> {_safe(hz['who_is_at_risk'])}"
                        f"<br/><b>Immediate action:</b> {_safe(hz['immediate_action'])}", small), Spacer(1, 7)]

    # CAPA
    S.append(Paragraph("Corrective action plan", h2))
    rows = [[P(x, small) for x in ("Priority", "Action", "Owner", "Timeframe")]]
    for a in r["actions"]:
        rows.append([P(f"{a['priority']} {PRIORITIES[a['priority']]}", small), P(a["action"], small), P(a["owner"], small), P(a["timeframe"], small)])
    if len(rows) == 1:
        rows.append([P("-", small)] * 4)
    t = Table(rows, colWidths=[2.6 * cm, 8.2 * cm, 3.2 * cm, 3 * cm], repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")), ("GRID", (0, 0), (-1, -1), 0.4, line),
                           ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    S.append(t)

    if r["prevention"]:
        S.append(Paragraph("Preventive measures", h2))
        S += [Paragraph("&bull; " + _safe(p), body) for p in r["prevention"]]
    if r["references"]:
        S.append(Paragraph("Indicative references (verify before citing)", h2))
        S += [Paragraph("&bull; " + _safe(p), body) for p in r["references"]]
    S += [Paragraph("Notify", h2), P(r["contact"]), Paragraph("Answer to inspection question", h2), P(r["answer"])]

    doc.build(S, onFirstPage=decorate, onLaterPages=decorate)
    return buf.getvalue()
