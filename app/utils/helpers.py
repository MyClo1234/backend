import json
import io
import copy
from typing import Any, Dict, List, Optional
from PIL import Image

from app.ai.prompts.extraction_prompts import ENUMS, ALIASES, DEFAULT_OBJ

def _clamp01(x: Any, default: float = 0.2) -> float:
    try:
        v = float(x)
        if v != v:
            return default
        return max(0.0, min(1.0, v))
    except Exception:
        return default

def _as_str(x: Any, default: str = "unknown") -> str:
    if x is None:
        return default
    if isinstance(x, str):
        s = x.strip().lower()
        return s if s else default
    return str(x).strip().lower() or default

def _as_bool(x: Any, default: bool = False) -> bool:
    if isinstance(x, bool):
        return x
    if isinstance(x, str):
        s = x.strip().lower()
        if s in ("true", "1", "yes", "y"):
            return True
        if s in ("false", "0", "no", "n"):
            return False
    if isinstance(x, (int, float)):
        return bool(x)
    return default

def _as_list_str(x: Any) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [_as_str(i) for i in x if _as_str(i)]
    if isinstance(x, str):
        if "," in x:
            return [_as_str(i) for i in x.split(",") if _as_str(i)]
        return [_as_str(x)]
    return [_as_str(x)]

def _in_enum(value: str, enum_list: List[str]) -> str:
    v = _as_str(value)
    return v if v in enum_list else "unknown"

def _alias(kind: str, s: Any) -> str:
    v = _as_str(s)
    return ALIASES.get(kind, {}).get(v, v)

def normalize(obj: Dict[str, Any]) -> Dict[str, Any]:
    out = copy.deepcopy(DEFAULT_OBJ)

    cat = obj.get("category", {}) if isinstance(obj.get("category"), dict) else {}
    out["category"]["main"] = _in_enum(_alias("category_main", cat.get("main")), ENUMS["category_main"])
    out["category"]["sub"]  = _in_enum(_as_str(cat.get("sub")), ENUMS["category_sub"])
    out["category"]["confidence"] = _clamp01(cat.get("confidence"), out["category"]["confidence"])

    col = obj.get("color", {}) if isinstance(obj.get("color"), dict) else {}
    out["color"]["primary"] = _in_enum(_alias("color", col.get("primary")), ENUMS["color"])
    sec = [_in_enum(_alias("color", s), ENUMS["color"]) for s in _as_list_str(col.get("secondary", []))]
    out["color"]["secondary"] = [s for s in sec if s != "unknown"][:3]
    out["color"]["tone"] = _in_enum(_alias("tone", col.get("tone")), ENUMS["tone"])
    out["color"]["confidence"] = _clamp01(col.get("confidence"), out["color"]["confidence"])

    pat = obj.get("pattern", {}) if isinstance(obj.get("pattern"), dict) else {}
    out["pattern"]["type"] = _in_enum(_as_str(pat.get("type")), ENUMS["pattern"])
    out["pattern"]["confidence"] = _clamp01(pat.get("confidence"), out["pattern"]["confidence"])

    mat = obj.get("material", {}) if isinstance(obj.get("material"), dict) else {}
    out["material"]["guess"] = _in_enum(_as_str(mat.get("guess")), ENUMS["material"])
    out["material"]["confidence"] = _clamp01(mat.get("confidence"), out["material"]["confidence"])

    fit = obj.get("fit", {}) if isinstance(obj.get("fit"), dict) else {}
    out["fit"]["type"] = _in_enum(_as_str(fit.get("type")), ENUMS["fit"])
    out["fit"]["confidence"] = _clamp01(fit.get("confidence"), out["fit"]["confidence"])

    det = obj.get("details", {}) if isinstance(obj.get("details"), dict) else {}
    out["details"]["neckline"] = _in_enum(_alias("neckline", det.get("neckline")), ENUMS["neckline"])
    out["details"]["sleeve"] = _in_enum(_as_str(det.get("sleeve")), ENUMS["sleeve"])
    out["details"]["length"] = _in_enum(_as_str(det.get("length")), ENUMS["length"])
    closure = [_in_enum(_alias("closure", c), ENUMS["closure"]) for c in _as_list_str(det.get("closure", ["unknown"]))]
    out["details"]["closure"] = (closure[:3] if closure else ["unknown"])
    out["details"]["print_or_logo"] = _as_bool(det.get("print_or_logo"), False)

    out["style_tags"] = [_in_enum(_as_str(t), ENUMS["style_tags"]) for t in _as_list_str(obj.get("style_tags", []))]
    out["style_tags"] = [t for t in out["style_tags"] if t != "unknown"][:8]

    sc = obj.get("scores", {}) if isinstance(obj.get("scores"), dict) else {}
    out["scores"]["formality"] = _clamp01(sc.get("formality"), out["scores"]["formality"])
    out["scores"]["warmth"] = _clamp01(sc.get("warmth"), out["scores"]["warmth"])
    out["scores"]["versatility"] = _clamp01(sc.get("versatility"), out["scores"]["versatility"])
    out["scores"]["season"] = [_in_enum(_as_str(s), ENUMS["season"]) for s in _as_list_str(sc.get("season", []))]
    out["scores"]["season"] = [s for s in out["scores"]["season"] if s != "unknown"][:4]

    meta = obj.get("meta", {}) if isinstance(obj.get("meta"), dict) else {}
    out["meta"]["is_layering_piece"] = _as_bool(meta.get("is_layering_piece"), out["meta"]["is_layering_piece"])
    notes = meta.get("notes", None)
    out["meta"]["notes"] = None if notes is None else str(notes)

    out["confidence"] = _clamp01(obj.get("confidence"), out["confidence"])
    return out

def load_image_from_bytes(image_bytes: bytes) -> Image.Image:
    """Load image from bytes and convert to RGB"""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return img
