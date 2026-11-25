"""Reusable HTML components. All user/model text is escaped."""
import html
import re

import streamlit as st

from .. import risk
from ..config import VERSION
from ..risk import BAND_COLOR, LIKELIHOOD, SEVERITY


def esc(x) -> str:
    return html.escape(str(x if x is not None else "")).replace("\n", " ")


def flat(s: str) -> str:
    return re.sub(r"\n\s*", "", s).strip()


def render(s: str):
    st.markdown(flat(s), unsafe_allow_html=True)


SCAN = """<div class="scan"><div class="scan-plane"><div class="ring r1"></div><div class="ring r2"></div>
<div class="ring r3"></div><div class="ring r4"></div><div class="sweep"></div>
<span class="pin p1"></span><span class="pin p2"></span><span class="pin p3"></span></div></div>"""


def chip(text, color="#8a93a5") -> str:
    return f'<span class="hl-chip" style="color:{color};border-color:{color}55;background:{color}1f">{esc(text)}</span>'


def band_chip(band) -> str:
    return chip(band, BAND_COLOR.get(band, "#8a93a5"))


def label(text):
    render(f'<div class="hl-label">{esc(text)}</div>')


def page_header(title, sub, crumb="Workspace", chips=()):
    ch = "".join(chip(t, c) for t, c in chips)
    render(f'<div class="hl-head"><div><div class="hl-crumb">HazardLens<i>/</i>{esc(crumb)}</div>'
           f'<h1 class="hl-title">{esc(title)}</h1><p class="hl-sub">{esc(sub)}</p><div class="hl-chips">{ch}</div></div>{SCAN}</div>')


def kpi(lbl, value, sub="", color="#e6e9ef") -> str:
    return (f'<div class="hl-kpi" style="--k:{color}"><div class="k-l">{esc(lbl)}</div>'
            f'<div class="k-v">{esc(value)}</div><div class="k-s">{esc(sub)}</div></div>')


def panel(title, body_html, raw=False):
    body = body_html if raw else f"<p>{esc(body_html)}</p>"
    render(f'<div class="hl-panel"><h4>{esc(title)}</h4>{body}</div>')


def bullet_list(items) -> str:
    return "<ul>" + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>" if items else "<p>-</p>"


def gauge(score, color, caption) -> str:
    total = 282.74
    dash = total * max(0, min(100, score)) / 100
    return (f'<div class="hl-gauge"><svg viewBox="0 0 200 112"><path d="M10 105 A90 90 0 0 1 190 105" fill="none" '
            f'stroke="rgba(255,255,255,.08)" stroke-width="13" stroke-linecap="round"/><path d="M10 105 A90 90 0 0 1 190 105" '
            f'fill="none" stroke="{color}" stroke-width="13" stroke-linecap="round" stroke-dasharray="{dash:.1f} {total}" '
            f'style="filter:drop-shadow(0 0 8px {color}88)"/></svg><div class="g-val" style="color:{color}">{score}</div>'
            f'<div class="g-cap">{esc(caption)}</div></div>')


def matrix(hazards=None, counts=None) -> str:
    cells = []
    for l in range(5, 0, -1):
        cells.append(f'<div class="mx-ax"><b>{l}</b>{LIKELIHOOD[l]}</div>')
        for s in range(1, 6):
            sc = l * s
            col = BAND_COLOR[risk.band_for(sc)]
            inner = ""
            if hazards:
                inner = "".join(f'<span class="mx-dot">{esc(h["ref"])}</span>' for h in hazards
                                if h["likelihood"] == l and h["severity"] == s)
            if counts and counts.get((l, s)):
                inner = f'<span class="mx-n">{counts[(l, s)]}</span>'
            cells.append(f'<div class="mx-c" style="background:{col}2e;border-color:{col}66"><em>{sc}</em>{inner}</div>')
    cells.append('<div class="mx-ax"></div>')
    for s in range(1, 6):
        cells.append(f'<div class="mx-ax x"><b>{s}</b>{SEVERITY[s]}</div>')
    return (f'<div class="mx">{"".join(cells)}</div><div class="mx-cap">Likelihood (rows) × Severity (columns)</div>'
            f'<div class="legend">' + "".join(f'<span style="--c:{BAND_COLOR[b]}">{b}</span>' for b in risk.BANDS) + "</div>")


def hazard_card(h) -> str:
    c = BAND_COLOR[h["band"]]
    return (f'<div class="hl-hz" style="--c:{c}"><div class="hz-top"><span class="hz-ref">{esc(h["ref"])}</span>'
            f'{band_chip(h["band"])}{chip(h["category"])}{chip(h["zone"])}<span class="hz-name">{esc(h["name"])}</span>'
            f'<span class="hz-sc">L{h["likelihood"]} × S{h["severity"]} = <b>{h["score"]}</b></span></div>'
            f'<div class="hz-desc">{esc(h["description"])}</div><div class="hz-grid">'
            f'<div><b>Consequence</b>{esc(h["consequence"] or "-")}</div><div><b>At risk</b>{esc(h["who_is_at_risk"])}</div>'
            f'<div><b>Immediate action</b>{esc(h["immediate_action"])}</div></div></div>')


def bars(rows) -> str:
    """rows: list of (label, value, color)."""
    mx = max([v for _, v, _ in rows] + [1])
    return '<div class="bars">' + "".join(
        f'<div class="b"><span>{esc(l)}</span><div class="t"><div class="f" style="--c:{c};width:{v / mx * 100:.0f}%"></div></div>'
        f'<span class="n">{v}</span></div>' for l, v, c in rows) + "</div>"


def table(headers, rows) -> str:
    """rows: list of lists of ready-to-render HTML strings."""
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in r) + "</tr>" for r in rows)
    return f'<table class="hl-table"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'
