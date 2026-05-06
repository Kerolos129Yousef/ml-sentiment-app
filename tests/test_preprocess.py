"""Tests for text preprocessing."""

from src.preprocess import clean_text, validate_input


def test_clean_text_removes_urls():
    text = "Check out https://example.com for more"
    result = clean_text(text)
    assert "https://" not in result


def test_clean_text_removes_html():
    text = "This is <b>bold</b> text"
    result = clean_text(text)
    assert "<b>" not in result
    assert "bold" in result


def test_clean_text_normalizes_whitespace():
    text = "Too   many    spaces"
    result = clean_text(text)
    assert result == "Too many spaces"


def test_validate_input_valid():
    assert validate_input("Hello world") is True


def test_validate_input_empty():
    assert validate_input("") is False
    assert validate_input("   ") is False


def test_validate_input_non_string():
    assert validate_input(123) is False
    assert validate_input(None) is False
