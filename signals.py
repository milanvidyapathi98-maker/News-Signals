"""Step 3 – Turn scored headlines into one score and a BUY / SELL / HOLD signal."""

import math
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

import config
from news_fetcher import get_news
from sentiment import score_articles


def aggregate(articles: list[dict]) -> float:
    """Recency-weighted average sentiment, range -1 .. +1."""
    if not articles:
        return 0.0
    now = datetime.now(timezone.utc)
    total, weights = 0.0, 0.0
    for a in articles:
        age_h = (now - a["published"]).total_seconds() / 3600
        w = 0.5 ** (age_h / config.HALF_LIFE_HOURS)
        a["weight"] = w
        total += w * a["sentiment"]
        weights += w
    return total / weights if weights else 0.0


def price_trend(ticker: str) -> dict:
    """Price history, 50-day moving average and trend (price above/below MA50)."""
    empty = {"price": None, "ma50": None, "trend": "unknown", "change_pct": None,
             "currency": "", "history": None}
    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="6mo")["Close"].dropna()
        if len(hist) < 50:
            return empty
        ma = hist.rolling(50).mean()
        price, ma50 = float(hist.iloc[-1]), float(ma.iloc[-1])
        try:
            currency = tk.fast_info["currency"] or ""
        except Exception:
            currency = ""
        return {
            "price": price,
            "ma50": ma50,
            "trend": "up" if price > ma50 else "down",
            "change_pct": float(hist.iloc[-1] / hist.iloc[-2] - 1) * 100,
            "currency": currency,
            "history": pd.DataFrame({"Close": hist, "MA50": ma}),
        }
    except Exception:
        return empty


def decide(score: float, n: int, trend: str, require_trend: bool) -> tuple[str, str]:
    """Return (signal, reason)."""
    if n < config.MIN_HEADLINES:
        return "HOLD", f"Only {n} recent headlines – not enough to judge."
    if score > config.BUY_THRESHOLD:
        if require_trend and trend == "down":
            return "HOLD", "News is positive, but price is below its 50-day average."
        return "BUY", "Recent news is clearly positive."
    if score < config.SELL_THRESHOLD:
        if require_trend and trend == "up":
            return "HOLD", "News is negative, but price is still above its 50-day average."
        return "SELL", "Recent news is clearly negative."
    return "HOLD", "News is mixed or neutral."


def analyse(ticker: str, require_trend: bool = True) -> dict:
    articles = score_articles(get_news(ticker))
    score = aggregate(articles)
    tech = price_trend(ticker)
    signal, reason = decide(score, len(articles), tech["trend"], require_trend)
    counts = {k: sum(a["label"] == k for a in articles) for k in ("positive", "neutral", "negative")}
    return {
        "ticker": ticker, "score": score, "signal": signal, "reason": reason,
        "headlines": len(articles), "counts": counts, "articles": articles, **tech,
    }


if __name__ == "__main__":
    # Quick test from the terminal:  python signals.py
    for t in config.DEFAULT_TICKERS:
        r = analyse(t)
        print(f"{t:8} {r['signal']:5} score={r['score']:+.2f}  "
              f"headlines={r['headlines']}  {r['reason']}")
