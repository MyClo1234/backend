import pytest
from fastapi import HTTPException

from app.utils.validators import validate_file_extension

def test_validate_file_extension_valid():
    """Valid extensions should be normalized to lowercase (including dot)."""
    assert validate_file_extension("image.jpg") == ".jpg"
    assert validate_file_extension("image.png") == ".png"
    assert validate_file_extension("test.JPEG") == ".jpeg"

def test_validate_file_extension_invalid():
    """Invalid/missing extensions should raise HTTPException."""
    with pytest.raises(HTTPException):
        validate_file_extension("file.txt")
    with pytest.raises(HTTPException):
        validate_file_extension("script.py")
    with pytest.raises(HTTPException):
        validate_file_extension("image")
