"""Text preprocessing utilities."""

import re


def clean_text(text: str) -> str:
    """Clean and normalize input text for sentiment analysis."""
    # Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    # Remove HTML tags
    text = re.sub(r"<.*?>", "", text)
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def validate_input(text) -> bool:
    """Validate that input is a non-empty string."""
    if not isinstance(text, str):
        return False
    if len(text.strip()) == 0:
        return False
    return True
