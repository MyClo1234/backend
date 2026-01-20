import json
from datetime import datetime
from PIL import Image

from app.core.constants import USER_PROMPT, DEFAULT_OBJ, ENUMS, REQUIRED_TOP_KEYS
from app.utils.json_parser import parse_json_from_text
from app.utils.validators import validate_schema
from app.utils.helpers import normalize, load_image_from_bytes
from app.services.gemini_client import gemini_client

class AttributeExtractor:
    def build_retry_prompt(self, errors: list) -> str:
        return f"""Fix your output to be VALID JSON and match the schema EXACTLY.

Errors:
- {chr(10).join(errors[:10])}

MUST:
- Return ONLY ONE JSON object. No extra text.
- Top-level keys must be EXACTLY: {sorted(list(REQUIRED_TOP_KEYS))}
- details.closure MUST be an ARRAY of strings (e.g. ["none"]).
- scores.season MUST be an ARRAY of strings (e.g. ["winter"]).
- All confidences must be 0.0~1.0.
- category.main must be one of {ENUMS["category_main"]}.
- color.tone must be one of {ENUMS["tone"]}.
- Use "unknown" if unsure.

Return corrected JSON ONLY.
"""

    def extract(self, image_bytes: bytes, retry_on_schema_fail: bool = True) -> dict:
        image = load_image_from_bytes(image_bytes)
        
        # First try
        try:
            raw1 = gemini_client.generate_content(USER_PROMPT, image)
            parsed1, repaired1 = parse_json_from_text(raw1)
        except Exception as e:
            # If generation fails completely
            out = json.loads(json.dumps(DEFAULT_OBJ))
            out["meta"]["notes"] = f"GEMINI_ERROR: {str(e)}"
            return out

        if parsed1 is None:
            out = json.loads(json.dumps(DEFAULT_OBJ))
            out["meta"]["notes"] = f"JSON_PARSE_FAILED. repaired_head={repaired1[:160]}"
            out["confidence"] = 0.1
            return out

        ok1, errs1 = validate_schema(parsed1)
        if ok1:
            return normalize(parsed1)

        # Retry
        if retry_on_schema_fail:
            prompt2 = self.build_retry_prompt(errs1)
            try:
                raw2 = gemini_client.generate_content(prompt2, image)
                parsed2, repaired2 = parse_json_from_text(raw2)

                if parsed2 is None:
                    out = json.loads(json.dumps(DEFAULT_OBJ))
                    out["meta"]["notes"] = f"RETRY_JSON_PARSE_FAILED. repaired_head={repaired2[:160]}"
                    out["confidence"] = 0.1
                    return out

                ok2, errs2 = validate_schema(parsed2)
                if ok2:
                    return normalize(parsed2)

                out = normalize(parsed2)
                out["meta"]["notes"] = (out["meta"]["notes"] or "")
                out["meta"]["notes"] = (out["meta"]["notes"] + f" | SCHEMA_INVALID_AFTER_RETRY: {errs2[:3]}")[:300]
                return out
            except Exception:
                pass

        # no retry or retry failed
        out = normalize(parsed1)
        out["meta"]["notes"] = (out["meta"]["notes"] or "")
        out["meta"]["notes"] = (out["meta"]["notes"] + f" | SCHEMA_INVALID_NO_RETRY: {errs1[:3]}")[:300]
        return out

extractor = AttributeExtractor()
