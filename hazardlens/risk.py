"""Risk engine: 5x5 likelihood x severity matrix, scoring and output normalisation.

The vision model only *describes* hazards and proposes likelihood/severity ratings (1-5).
All scores, bands and the overall index are computed here, deterministically.
"""
from datetime import datetime

from .config import CATEGORIES, TZ, ZONES

LIKELIHOOD = {1: "Rare", 2: "Unlikely", 3: "Possible", 4: "Likely", 5: "Almost certain"}
SEVERITY = {1: "Negligible", 2: "Minor", 3: "Moderate", 4: "Major", 5: "Catastrophic"}
BANDS = ["Low", "Medium", "High", "Critical"]
BAND_COLOR = {"Low": "#34a37a", "Medium": "#d6a73a", "High": "#e5792e", "Critical": "#d94a4a"}
PRIORITIES = {"P1": "Immediate", "P2": "Within 24 h", "P3": "Within 7 days"}


def band_for(score: int) -> str:
    """Standard 5x5 banding: 1-4 Low, 5-9 Medium, 10-14 High, 15-25 Critical."""
    if score <= 4:
        return "Low"
    if score <= 9:
        return "Medium"
    if score <= 14:
        return "High"
    return "Critical"


def _int(value, lo, hi, default):
    try:
        return max(lo, min(hi, int(float(value))))
    except (TypeError, ValueError):
        return default


def _match_zone(value) -> str:
    v = str(value or "").strip().lower().replace("-", " ").replace("_", " ").replace("centre", "center")
    for z in ZONES:
        if z.lower() == v:
            return z
    return "Center"


def _strlist(value) -> list:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return []


def risk_index(hazards: list) -> int:
    """0-100 index: driven by the worst hazard, small uplift for hazard count."""
    if not hazards:
        return 0
    top = max(h["score"] for h in hazards)
    return min(100, round(top / 25 * 100 + min(8, 2 * (len(hazards) - 1))))


def normalize(raw: dict) -> dict:
    raw = raw if isinstance(raw, dict) else {}
    hazards = []
    for h in raw.get("hazards") or []:
        if not isinstance(h, dict):
            continue
        l = _int(h.get("likelihood"), 1, 5, 3)
        s = _int(h.get("severity"), 1, 5, 3)
        cat = str(h.get("category", "Other")).strip().title()
        hazards.append({
            "name": str(h.get("name") or "Unnamed hazard"),
            "category": cat if cat in CATEGORIES else "Other",
            "zone": _match_zone(h.get("zone")),
            "likelihood": l, "severity": s, "score": l * s, "band": band_for(l * s),
            "description": str(h.get("description") or ""),
            "consequence": str(h.get("consequence") or ""),
            "who_is_at_risk": str(h.get("who_is_at_risk") or "-"),
            "immediate_action": str(h.get("immediate_action") or "-"),
        })
    hazards.sort(key=lambda x: x["score"], reverse=True)
    for i, h in enumerate(hazards, 1):
        h["ref"] = f"H{i}"

    actions = []
    for a in raw.get("corrective_actions") or []:
        if isinstance(a, dict) and a.get("action"):
            p = str(a.get("priority", "P2")).upper().strip()
            p = p if p in PRIORITIES else "P2"
            actions.append({"hazard": str(a.get("hazard") or ""), "action": str(a["action"]), "priority": p,
                            "owner": str(a.get("owner") or "Site supervisor"),
                            "timeframe": str(a.get("timeframe") or PRIORITIES[p])})
    if not actions:  # derive a plan from the hazards if the model omitted it
        for h in hazards:
            p = {"Critical": "P1", "High": "P1", "Medium": "P2", "Low": "P3"}[h["band"]]
            actions.append({"hazard": h["ref"], "action": h["immediate_action"], "priority": p,
                            "owner": "Site supervisor", "timeframe": PRIORITIES[p]})
    actions.sort(key=lambda a: a["priority"])

    top = hazards[0]["score"] if hazards else 0
    return {
        "summary": str(raw.get("scene_summary") or ""),
        "primary_hazard": str(raw.get("primary_hazard") or (hazards[0]["name"] if hazards else "No significant hazard")),
        "observations": _strlist(raw.get("positive_observations")),
        "hazards": hazards, "actions": actions,
        "prevention": _strlist(raw.get("preventive_measures")),
        "references": _strlist(raw.get("reference_standards")),
        "contact": str(raw.get("who_to_contact") or "Local emergency services (112)."),
        "answer": str(raw.get("answer_to_user_query") or ""),
        "confidence": _int(raw.get("confidence"), 0, 100, 75),
        "overall_score": top,
        "overall_band": band_for(top) if hazards else "Low",
        "risk_index": risk_index(hazards),
    }


def make_id(seq: int, now: datetime = None) -> str:
    now = now or datetime.now(TZ)
    return f"HL-{now:%y%m%d}-{seq:03d}"


def matrix_counts(hazards) -> dict:
    counts = {}
    for h in hazards:
        key = (h["likelihood"], h["severity"])
        counts[key] = counts.get(key, 0) + 1
    return counts
