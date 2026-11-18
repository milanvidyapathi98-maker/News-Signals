"""Step 2 – Score each headline with FinBERT (positive / negative / neutral)."""

from functools import lru_cache

from transformers import pipeline

import config

SIGN = {"positive": 1, "negative": -1, "neutral": 0}


@lru_cache(maxsize=1)
def _model():
    # Downloads the model (~400 MB) the first time, then uses the local copy
    return pipeline("text-classification", model=config.SENTIMENT_MODEL)


def score_articles(articles: list[dict]) -> list[dict]:
    """Adds 'label', 'confidence' and 'sentiment' (-1..+1) to each article."""
    if not articles:
        return []
    # Headline + start of summary gives the model a bit more context
    texts = [(a["title"] + ". " + a["summary"])[:500] for a in articles]
    results = _model()(texts, truncation=True)
    for a, r in zip(articles, results):
        label = r["label"].lower()
        a["label"] = label
        a["confidence"] = float(r["score"])
        a["sentiment"] = SIGN[label] * float(r["score"])
    return articles
