from typing import Any
import re


def clean_text(text: str) -> str:
    """Clean and normalize input text for sentiment analysis."""
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def validate_input(text: Any) -> bool:
    """Validate that input is a non-empty string."""
    if not isinstance(text, str):
        return False
    if len(text.strip()) == 0:
        return False
    return True
