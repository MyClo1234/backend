from typing import Any, Dict, List, Tuple
from app.core.constants import REQUIRED_TOP_KEYS

def _is_num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not (isinstance(x, float) and x != x)

def _in_01(x: Any) -> bool:
    return _is_num(x) and 0.0 <= float(x) <= 1.0

def validate_schema(obj: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errs: List[str] = []
    if not isinstance(obj, dict):
        return False, ["Top-level is not an object/dict"]

    keys = set(obj.keys())
    if keys != REQUIRED_TOP_KEYS:
        missing = sorted(list(REQUIRED_TOP_KEYS - keys))
        extra = sorted(list(keys - REQUIRED_TOP_KEYS))
        if missing:
            errs.append(f"Missing top-level keys: {missing}")
        if extra:
            errs.append(f"Extra top-level keys not allowed: {extra}")

    def _must_dict(name):
        v = obj.get(name)
        if not isinstance(v, dict):
            errs.append(f"{name} must be an object")
            return None
        return v

    cat = _must_dict("category")
    if cat:
        if not isinstance(cat.get("main"), str): errs.append("category.main must be string")
        if not isinstance(cat.get("sub"), str): errs.append("category.sub must be string")
        if not _in_01(cat.get("confidence")): errs.append("category.confidence must be number in [0,1]")

    col = _must_dict("color")
    if col:
        if not isinstance(col.get("primary"), str): errs.append("color.primary must be string")
        sec = col.get("secondary")
        if not isinstance(sec, list) or any(not isinstance(x, str) for x in sec):
            errs.append("color.secondary must be [string]")
        if not isinstance(col.get("tone"), str): errs.append("color.tone must be string")
        if not _in_01(col.get("confidence")): errs.append("color.confidence must be number in [0,1]")

    pat = _must_dict("pattern")
    if pat:
        if not isinstance(pat.get("type"), str): errs.append("pattern.type must be string")
        if not _in_01(pat.get("confidence")): errs.append("pattern.confidence must be number in [0,1]")

    mat = _must_dict("material")
    if mat:
        if not isinstance(mat.get("guess"), str): errs.append("material.guess must be string")
        if not _in_01(mat.get("confidence")): errs.append("material.confidence must be number in [0,1]")

    fit = _must_dict("fit")
    if fit:
        if not isinstance(fit.get("type"), str): errs.append("fit.type must be string")
        if not _in_01(fit.get("confidence")): errs.append("fit.confidence must be number in [0,1]")

    det = _must_dict("details")
    if det:
        if not isinstance(det.get("neckline"), str): errs.append("details.neckline must be string")
        if not isinstance(det.get("sleeve"), str): errs.append("details.sleeve must be string")
        if not isinstance(det.get("length"), str): errs.append("details.length must be string")
        clo = det.get("closure")
        if not isinstance(clo, list) or any(not isinstance(x, str) for x in clo):
            errs.append("details.closure must be [string]")
        if not isinstance(det.get("print_or_logo"), bool):
            errs.append("details.print_or_logo must be boolean")

    tags = obj.get("style_tags")
    if not isinstance(tags, list) or any(not isinstance(x, str) for x in tags):
        errs.append("style_tags must be [string]")

    sc = _must_dict("scores")
    if sc:
        if not _in_01(sc.get("formality")): errs.append("scores.formality must be number in [0,1]")
        if not _in_01(sc.get("warmth")): errs.append("scores.warmth must be number in [0,1]")
        if not _in_01(sc.get("versatility")): errs.append("scores.versatility must be number in [0,1]")
        seas = sc.get("season")
        if not isinstance(seas, list) or any(not isinstance(x, str) for x in seas):
            errs.append("scores.season must be [string]")

    meta = _must_dict("meta")
    if meta:
        if not isinstance(meta.get("is_layering_piece"), bool):
            errs.append("meta.is_layering_piece must be boolean")
        notes = meta.get("notes")
        if not (notes is None or isinstance(notes, str)):
            errs.append("meta.notes must be string|null")

    if not _in_01(obj.get("confidence")):
        errs.append("confidence must be number in [0,1]")

    return (len(errs) == 0), errs
