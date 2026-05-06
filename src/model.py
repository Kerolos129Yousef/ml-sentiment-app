"""Sentiment classification model using TextBlob."""

from textblob import TextBlob

from src.preprocess import clean_text


def predict_sentiment(text: str) -> dict:
    """Predict sentiment of input text.

    Returns a dictionary with label and confidence score.
    """
    cleaned = clean_text(text)
    blob = TextBlob(cleaned)
    polarity = blob.sentiment.polarity

    if polarity > 0.1:
        label = "positive"
    elif polarity < -0.1:
        label = "negative"
    else:
        label = "neutral"

    confidence = round(abs(polarity), 4)
    return {"label": label, "confidence": confidence}
