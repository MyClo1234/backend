from typing import Dict, List

# -----------------------------
# Enums
# -----------------------------
ENUMS = {
    "category_main": ["outer", "top", "bottom", "onepiece", "shoes", "bag", "accessory"],
    "category_sub": [
        "coat", "puffer", "jacket", "blazer", "cardigan", "hoodie", "sweatshirt",
        "shirt", "tshirt", "knit", "sweater", "slacks", "jeans", "shorts",
        "skirt", "dress", "sneakers", "loafers", "heels", "boots",
        "bag", "cap", "hat", "scarf", "belt", "other", "unknown"
    ],
    "color": [
        "black", "white", "gray", "navy", "blue", "skyblue", "beige", "brown", "khaki",
        "green", "red", "pink", "purple", "yellow", "orange", "cream", "other", "unknown"
    ],
    "tone": ["dark", "mid", "light", "pastel", "vivid", "unknown"],
    "pattern": ["solid", "stripe", "check", "dot", "graphic", "floral", "other", "unknown"],
    "material": ["cotton", "denim", "knit", "wool", "leather", "poly", "linen", "other", "unknown"],
    "fit": ["slim", "regular", "oversized", "wide", "unknown"],
    "neckline": ["crew", "vneck", "collar", "turtleneck", "hood", "unknown"],
    "sleeve": ["sleeveless", "short", "long", "unknown"],
    "length": ["cropped", "waist", "hip", "long", "unknown"],
    "closure": ["zipper", "button", "open", "none", "unknown"],
    "style_tags": ["minimal", "classic", "street", "sporty", "feminine", "vintage", "business", "formal", "casual", "other"],
    "season": ["spring", "summer", "fall", "winter"],
}

ALIASES = {
    "category_main": {"clothing": "top", "sweater": "top", "knitwear": "top"},
    "color": {"dark blue": "navy", "navy blue": "navy", "light blue": "skyblue"},
    "neckline": {"round": "crew", "crew neck": "crew", "crewneck": "crew"},
    "closure": {"no closure": "none", "none": "none"},
    "tone": {"navy": "dark"},
}

REQUIRED_TOP_KEYS = {"category", "color", "pattern", "material", "fit", "details", "style_tags", "scores", "meta", "confidence"}

DEFAULT_OBJ = {
    "category": {"main": "unknown", "sub": "unknown", "confidence": 0.2},
    "color": {"primary": "unknown", "secondary": [], "tone": "unknown", "confidence": 0.2},
    "pattern": {"type": "unknown", "confidence": 0.2},
    "material": {"guess": "unknown", "confidence": 0.2},
    "fit": {"type": "unknown", "confidence": 0.2},
    "details": {"neckline": "unknown", "sleeve": "unknown", "length": "unknown", "closure": ["unknown"], "print_or_logo": False},
    "style_tags": [],
    "scores": {"formality": 0.3, "warmth": 0.3, "season": [], "versatility": 0.5},
    "meta": {"is_layering_piece": False, "notes": None},
    "confidence": 0.2,
}

SYSTEM_PROMPT = (
    "You are a clothing-attribute extractor.\n"
    "You MUST output ONLY a valid JSON object. No extra text.\n"
    "Follow the schema EXACTLY.\n"
    "If uncertain, use 'unknown' or null and lower confidence.\n"
)

USER_PROMPT = f"""Extract attributes for the single clothing item in the image.

Return ONLY ONE JSON object with EXACTLY these top-level keys:
category, color, pattern, material, fit, details, style_tags, scores, meta, confidence

Schema (types):
{{
  "category": {{"main": string, "sub": string, "confidence": number}},
  "color": {{"primary": string, "secondary": [string], "tone": string, "confidence": number}},
  "pattern": {{"type": string, "confidence": number}},
  "material": {{"guess": string, "confidence": number}},
  "fit": {{"type": string, "confidence": number}},
  "details": {{
    "neckline": string,
    "sleeve": string,
    "length": string,
    "closure": [string],
    "print_or_logo": boolean
  }},
  "style_tags": [string],
  "scores": {{
    "formality": number,
    "warmth": number,
    "season": [string],
    "versatility": number
  }},
  "meta": {{"is_layering_piece": boolean, "notes": string|null}},
  "confidence": number
}}

Critical rules:
- JSON only. No markdown. No commentary. No trailing text.
- details.closure MUST be an ARRAY, e.g. ["none"] (never a string).
- scores.season MUST be an ARRAY, e.g. ["winter"] (never a string).
- confidence fields must be 0.0~1.0
- Use lowercase tokens (short). If unsure use "unknown".
- category.main must be one of {ENUMS["category_main"]}.
- color.tone must be one of {ENUMS["tone"]}.
"""
