"""Vision-model layer (Groq). No Streamlit imports so it is unit-testable."""
import base64
import json
import re

from .config import CATEGORIES, MODELS, ZONES


def make_client(api_key: str):
    import httpx
    from groq import Groq
    return Groq(api_key=api_key, http_client=httpx.Client())


def build_system_prompt(site_type: str, max_hazards: int, language: str) -> str:
    return f"""You are a senior EHS (environment, health & safety) inspector. Assess the photo for hazards.
Scene type: {site_type}. Respond with ONE valid JSON object only - no markdown, no commentary:
{{
 "scene_summary": "1-2 factual sentences describing what is visible",
 "primary_hazard": "short title of the most serious hazard, or 'No significant hazard'",
 "confidence": <integer 0-100, how sure you are given image quality and visibility>,
 "hazards": [{{
   "name": "short name",
   "category": "one of {CATEGORIES}",
   "zone": "one of {ZONES} - where in the image it appears",
   "likelihood": <1-5>, "severity": <1-5>,
   "description": "what it is and why it is dangerous (2-3 sentences)",
   "consequence": "most credible worst-case outcome",
   "who_is_at_risk": "people or assets exposed",
   "immediate_action": "one specific step to take right now"}}],
 "corrective_actions": [{{
   "hazard": "H-style name or short reference", "action": "specific corrective or preventive action",
   "priority": "P1 (immediate) | P2 (within 24h) | P3 (within 7 days)",
   "owner": "responsible role, e.g. Site supervisor, Electrician, Municipal authority",
   "timeframe": "e.g. Immediate, 24 hours, 7 days"}}],
 "positive_observations": ["controls or good practices visible, if any"],
 "preventive_measures": ["2-5 specific long-term measures"],
 "reference_standards": ["indicative applicable standards/regulations, e.g. NBC 2016, IS 732, OSHA 1910.303"],
 "who_to_contact": "who to call or notify",
 "answer_to_user_query": "direct, practical answer to the user's question"
}}
Rating scales. likelihood: 1 rare, 2 unlikely, 3 possible, 4 likely, 5 almost certain without intervention.
severity: 1 negligible (first aid), 2 minor (medical treatment), 3 moderate (lost-time injury / notable damage),
4 major (permanent disability / major damage), 5 catastrophic (fatality or multiple casualties).
List at most {max_hazards} hazards, most serious first. Judge only what is visible; do not invent hazards.
Write all text values in {language}. Keep JSON keys, category names, zone names and priority codes in English.
If nothing hazardous is visible return an empty hazards list."""


def models_order(preferred: str) -> list:
    return [preferred] + [m for m in MODELS.values() if m != preferred]


def is_model_unavailable(err: Exception) -> bool:
    s = str(err).lower()
    return any(t in s for t in ("model_not_found", "404", "decommission", "does not exist", "no longer supported"))


def complete(client, messages, preferred, json_mode=False, max_tokens=3500):
    """Call the preferred model, falling back through MODELS on failure. Returns (text, model_used)."""
    errors = []
    for model in models_order(preferred):
        try:
            kwargs = dict(model=model, messages=messages, temperature=0.2, max_tokens=max_tokens)
            try:
                if json_mode:
                    resp = client.chat.completions.create(response_format={"type": "json_object"}, **kwargs)
                else:
                    resp = client.chat.completions.create(**kwargs)
            except Exception as e:
                if json_mode and not is_model_unavailable(e):
                    resp = client.chat.completions.create(**kwargs)  # JSON mode unsupported -> plain retry
                else:
                    raise
            text = re.sub(r"<think>.*?</think>", "", resp.choices[0].message.content or "", flags=re.S).strip()
            if not text:
                raise RuntimeError("empty response")
            return text, model
        except Exception as e:
            errors.append(f"{model}: {str(e)[:150]}")
    raise RuntimeError("All vision models failed. " + " | ".join(errors))


def parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    m = re.search(r"\{.*\}", text, flags=re.S)
    return json.loads(m.group(0) if m else text)


def data_url(jpeg: bytes) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(jpeg).decode()


def analyze(client, jpeg, question, site_type, max_hazards, language, preferred):
    messages = [
        {"role": "system", "content": build_system_prompt(site_type, max_hazards, language)},
        {"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": data_url(jpeg)}},
            {"type": "text", "text": f"Inspection question: {question}"}]},
    ]
    text, used = complete(client, messages, preferred, json_mode=True)
    return parse_json(text), used


def follow_up(client, jpeg, result_json, history, question, language, preferred):
    past = "\n".join(f"Q: {q}\nA: {a}" for q, a in history[-4:])
    messages = [
        {"role": "system", "content": "You are a senior EHS inspector answering follow-up questions about an "
                                      "inspection photo and its earlier assessment. Be concise, practical and "
                                      f"specific (max 150 words, plain text). Reply in {language}."},
        {"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": data_url(jpeg)}},
            {"type": "text", "text": f"Earlier assessment: {result_json[:3000]}\n\nPrevious follow-ups:\n{past}\n\nNew question: {question}"}]},
    ]
    text, _ = complete(client, messages, preferred, json_mode=False, max_tokens=1500)
    return text
