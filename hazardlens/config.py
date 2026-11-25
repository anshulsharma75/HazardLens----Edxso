"""Central configuration and constants."""
from datetime import timedelta, timezone

APP_NAME = "HazardLens"
VERSION = "2.0.0"
TZ = timezone(timedelta(hours=5, minutes=30))  # IST

# Order = fallback priority. If a model is retired, the next one is tried automatically.
MODELS = {
    "Qwen 3.8 · 27B": "qwen/qwen3.8-27b",
    "Qwen 3.6 · 27B": "qwen/qwen3.6-27b",
    "Muse Spark Open": "meta-models/muse-spark-open",
}

SITE_TYPES = ["General", "Road & Traffic", "Construction Site", "Industrial / Factory",
              "Home & Household", "Electrical & Fire", "Water & Drainage", "Public Place"]

LANGUAGES = {
    "English": "English",
    "Hindi": "Hindi (Devanagari script)",
    "Hinglish": "Hinglish (Hindi written in Latin script)",
}

DEPTH = {"Standard · up to 4 hazards": 4, "Detailed · up to 8 hazards": 8}

CATEGORIES = ["Electrical", "Fire", "Structural", "Chemical", "Traffic",
              "Water", "Biological", "Mechanical", "Ergonomic", "Other"]

# 3x3 grid used to approximately locate a hazard inside the image
ZONES = ["Top left", "Top center", "Top right",
         "Middle left", "Center", "Middle right",
         "Bottom left", "Bottom center", "Bottom right"]

STATUSES = ["Open", "In progress", "Closed"]

PRESETS = [
    "Quick questions",
    "What is the primary danger shown in this image?",
    "List every safety hazard and rate its severity.",
    "Is it safe for people to be near this? What should they do?",
    "What could go wrong if this is ignored for 24 hours?",
    "Who should be contacted and what should be done right now?",
]

EMERGENCY = [("112", "National emergency number"), ("100", "Police"), ("101", "Fire brigade"),
             ("102 / 108", "Ambulance"), ("1078", "NDMA disaster management")]
