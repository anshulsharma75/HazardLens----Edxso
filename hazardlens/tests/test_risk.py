import io

from PIL import Image

from hazardlens import ai, imaging, report, risk


def test_band_thresholds():
    assert [risk.band_for(s) for s in (1, 4, 5, 9, 10, 14, 15, 25)] == [
        "Low", "Low", "Medium", "Medium", "High", "High", "Critical", "Critical"]


def test_normalize_clamps_and_sorts():
    raw = {"hazards": [
        {"name": "a", "likelihood": 99, "severity": -3, "zone": "nowhere", "category": "bogus"},
        {"name": "b", "likelihood": "5", "severity": 4, "zone": "top-center", "category": "fire"}]}
    res = risk.normalize(raw)
    assert [h["ref"] for h in res["hazards"]] == ["H1", "H2"]
    assert res["hazards"][0]["name"] == "b" and res["hazards"][0]["score"] == 20
    assert res["hazards"][0]["zone"] == "Top center" and res["hazards"][0]["category"] == "Fire"
    assert res["hazards"][1]["likelihood"] == 5 and res["hazards"][1]["severity"] == 1
    assert res["hazards"][1]["category"] == "Other" and res["hazards"][1]["zone"] == "Center"
    assert res["overall_band"] == "Critical"


def test_empty_and_garbage_input():
    for raw in ({}, None, "x", {"hazards": "nope"}):
        res = risk.normalize(raw)
        assert res["overall_band"] == "Low" and res["risk_index"] == 0 and res["hazards"] == []


def test_actions_derived_when_missing():
    res = risk.normalize({"hazards": [{"name": "x", "likelihood": 5, "severity": 5, "immediate_action": "Evacuate"}]})
    assert res["actions"][0]["priority"] == "P1" and res["actions"][0]["action"] == "Evacuate"


def test_risk_index_bounds():
    hs = [{"score": 25}] * 10
    assert risk.risk_index(hs) == 100
    assert risk.risk_index([]) == 0


def test_json_parsing_and_model_errors():
    assert ai.parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert ai.parse_json('text before {"a": 2} after') == {"a": 2}
    assert ai.is_model_unavailable(Exception("Error code: 404 - model_not_found"))
    assert not ai.is_model_unavailable(Exception("rate limit exceeded"))
    assert ai.models_order("qwen/qwen3.6-27b")[0] == "qwen/qwen3.6-27b"


def _sample_record():
    buf = io.BytesIO()
    Image.new("RGB", (800, 600), (50, 70, 80)).save(buf, "JPEG")
    res = risk.normalize({"scene_summary": "s", "hazards": [
        {"name": "Water jet", "likelihood": 5, "severity": 3, "zone": "Top center"}]})
    jpeg = buf.getvalue()
    return {"id": "HL-000000-001", "time": "now", "site": "S", "location": "L", "inspector": "I", "site_type": "General",
            "question": "q ⚡", "model": "m", "status": "Open", "result": res, "jpeg": jpeg,
            "annotated": imaging.annotate(jpeg, res["hazards"]), "chat": []}


def test_reports_build():
    rec = _sample_record()
    assert report.build_pdf(rec)[:4] == b"%PDF"
    assert "Risk register" in report.build_markdown(rec)
