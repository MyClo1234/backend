import json
import re
from typing import Any, Optional, Tuple, Dict, List

def _first_balanced_json_object(s: str) -> Optional[str]:
    """Return the first balanced {{...}} JSON object substring found in s."""
    s = s.strip()
    start = s.find("{")
    if start == -1:
        return None

    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(s)):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        else:
            if ch == '"':
                in_str = True
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return s[start:i+1]
    return None

def _repair_json_like(s: str) -> str:
    s = s.strip()
    s = re.sub(r"^```(?:json)?\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    s = re.sub(r"\bNone\b", "null", s)
    s = re.sub(r"\bTrue\b", "true", s)
    s = re.sub(r"\bFalse\b", "false", s)
    s = re.sub(r",\s*([}}\]])", r"\1", s)
    if s.count('"') < 4 and s.count("'") > 4:
        s = s.replace("'", '"')
    return s

def _first_balanced_json_array(s: str) -> Optional[str]:
    """Return the first balanced [...] JSON array substring found in s."""
    s = s.strip()
    start = s.find("[")
    if start == -1:
        return None

    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(s)):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        else:
            if ch == '"':
                in_str = True
                continue
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    return s[start:i+1]
    return None

def parse_json_from_text(text: str) -> Tuple[Optional[Any], str]:
    """
    Parse JSON from text, supporting both dict and list.
    Returns: (parsed_object or None, repaired_text)
    """
    # Try to find JSON array first (for recommendations)
    array_candidate = _first_balanced_json_array(text)
    if array_candidate:
        repaired = _repair_json_like(array_candidate)
        try:
            obj = json.loads(repaired)
            if isinstance(obj, list):
                return obj, repaired
        except Exception:
            pass
    
    # Try to find JSON object (for attribute extraction)
    candidate = _first_balanced_json_object(text) or text
    repaired = _repair_json_like(candidate)
    try:
        obj = json.loads(repaired)
        if isinstance(obj, (dict, list)):
            return obj, repaired
        return None, repaired
    except Exception:
        return None, repaired
