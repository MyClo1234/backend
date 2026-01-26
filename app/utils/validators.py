import os
from typing import Any, Dict, List, Tuple, Optional
from fastapi import UploadFile, HTTPException
from app.ai.prompts.extraction_prompts import REQUIRED_TOP_KEYS
from app.core.config import Config


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
        if not isinstance(cat.get("main"), str):
            errs.append("category.main must be string")
        if not isinstance(cat.get("sub"), str):
            errs.append("category.sub must be string")
        if not _in_01(cat.get("confidence")):
            errs.append("category.confidence must be number in [0,1]")

    col = _must_dict("color")
    if col:
        if not isinstance(col.get("primary"), str):
            errs.append("color.primary must be string")
        sec = col.get("secondary")
        if not isinstance(sec, list) or any(not isinstance(x, str) for x in sec):
            errs.append("color.secondary must be [string]")
        if not isinstance(col.get("tone"), str):
            errs.append("color.tone must be string")
        if not _in_01(col.get("confidence")):
            errs.append("color.confidence must be number in [0,1]")

    pat = _must_dict("pattern")
    if pat:
        if not isinstance(pat.get("type"), str):
            errs.append("pattern.type must be string")
        if not _in_01(pat.get("confidence")):
            errs.append("pattern.confidence must be number in [0,1]")

    mat = _must_dict("material")
    if mat:
        if not isinstance(mat.get("guess"), str):
            errs.append("material.guess must be string")
        if not _in_01(mat.get("confidence")):
            errs.append("material.confidence must be number in [0,1]")

    fit = _must_dict("fit")
    if fit:
        if not isinstance(fit.get("type"), str):
            errs.append("fit.type must be string")
        if not _in_01(fit.get("confidence")):
            errs.append("fit.confidence must be number in [0,1]")

    # Details (Formerly nested, now top-level)
    if not isinstance(obj.get("neckline"), str):
        errs.append("neckline must be string")
    if not isinstance(obj.get("sleeve"), str):
        errs.append("sleeve must be string")
    if not isinstance(obj.get("length"), str):
        errs.append("length must be string")

    clo = obj.get("closure")
    if not isinstance(clo, list) or any(not isinstance(x, str) for x in clo):
        errs.append("closure must be [string]")

    # Legacy 'details' check or other details fields?
    # prompt NO LONGER returns 'details'. 'print_or_logo' is moved to meta?
    # Let's check prompt again. Prompt puts print_or_logo in meta.
    # So 'details' key should NOT exist or be ignored.

    tags = obj.get("style_tags")
    if not isinstance(tags, list) or any(not isinstance(x, str) for x in tags):
        errs.append("style_tags must be [string]")

    sc = _must_dict("scores")
    if sc:
        if not _in_01(sc.get("formality")):
            errs.append("scores.formality must be number in [0,1]")
        if not _in_01(sc.get("warmth")):
            errs.append("scores.warmth must be number in [0,1]")
        if not _in_01(sc.get("versatility")):
            errs.append("scores.versatility must be number in [0,1]")
        seas = sc.get("season")
        if not isinstance(seas, list) or any(not isinstance(x, str) for x in seas):
            errs.append("scores.season must be [string]")

    meta = _must_dict("meta")
    if meta:
        if not isinstance(meta.get("is_layering_piece"), bool):
            errs.append("meta.is_layering_piece must be boolean")
        if not isinstance(meta.get("print_or_logo"), bool):
            errs.append("meta.print_or_logo must be boolean")

        # layering_rank (1, 2, 3 check)
        lr = meta.get("layering_rank")
        if not isinstance(lr, int):
            errs.append("meta.layering_rank must be integer")
        elif lr not in [1, 2, 3]:
            errs.append("meta.layering_rank must be 1, 2, or 3")

        notes = meta.get("notes")
        if not (notes is None or isinstance(notes, str)):
            errs.append("meta.notes must be string|null")

    if not _in_01(obj.get("confidence")):
        errs.append("confidence must be number in [0,1]")

    return (len(errs) == 0), errs


def validate_uploaded_file(
    filename: Optional[str],
    content_type: Optional[str],
    file_size: int,
    max_size: int = Config.MAX_FILE_SIZE,
) -> None:
    """
    업로드된 파일 검증 (확장자, MIME 타입, 크기)

    Args:
        filename: 파일명
        content_type: MIME 타입
        file_size: 파일 크기 (bytes)
        max_size: 최대 파일 크기 (bytes)

    Raises:
        HTTPException: 검증 실패 시
    """
    # 파일명 검증
    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required. Please provide a filename for the uploaded file.",
        )

    # 확장자 검증
    filename_lower = filename.lower()
    file_ext = os.path.splitext(filename_lower)[1]

    if file_ext not in Config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(Config.ALLOWED_EXTENSIONS)}",
        )

    # MIME 타입 검증
    if content_type and content_type not in Config.ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid MIME type. Allowed: {', '.join(Config.ALLOWED_MIME_TYPES)}",
        )

    # 파일 크기 검증
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size ({max_size / (1024 * 1024):.1f}MB).",
        )


def validate_file_extension(filename: str) -> str:
    """
    파일 확장자 검증 및 정규화

    Args:
        filename: 파일명

    Returns:
        정규화된 확장자 (소문자, 점 포함)

    Raises:
        HTTPException: 허용되지 않은 확장자일 경우
    """
    _, ext = os.path.splitext(filename)
    ext_lower = ext.lower()

    if ext_lower not in Config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(sorted(Config.ALLOWED_EXTENSIONS))}",
        )

    return ext_lower
