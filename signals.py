"""Step 3 – Turn scored headlines into one score and a BUY / SELL / HOLD signal."""

from datetime import datetime, timezone

from urllib.parse import quote

import pandas as pd
import requests
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


def _prices_yfinance(ticker: str) -> tuple[pd.Series, str]:
    """Daily closing prices via the yfinance package."""
    tk = yf.Ticker(ticker)
    hist = tk.history(period="6mo")
    if hist is None or hist.empty:
        raise ValueError("no data returned")
    try:
        currency = tk.fast_info["currency"] or ""
    except Exception:
        currency = ""
    return hist["Close"].dropna(), currency


def _prices_yahoo_chart(ticker: str) -> tuple[pd.Series, str]:
    """Backup: Yahoo's chart endpoint called directly (works when yfinance is blocked/broken)."""
    for host in ("query2", "query1"):
        resp = requests.get(
            f"https://{host}.finance.yahoo.com/v8/finance/chart/{quote(ticker)}",
            params={"range": "6mo", "interval": "1d"},
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            timeout=10,
        )
        if resp.status_code == 200:
            break
    resp.raise_for_status()
    result = resp.json()["chart"]["result"][0]
    closes = result["indicators"]["quote"][0]["close"]
    index = pd.to_datetime(result["timestamp"], unit="s")
    return pd.Series(closes, index=index, dtype="float64").dropna(), result["meta"].get("currency", "")


def price_trend(ticker: str) -> dict:
    """Price history, 50-day moving average and trend (price above/below MA50)."""
    result = {"price": None, "ma50": None, "trend": "unknown", "change_pct": None,
              "currency": "", "history": None, "price_error": ""}
    errors = []
    for name, source in (("yfinance", _prices_yfinance), ("Yahoo chart", _prices_yahoo_chart)):
        try:
            hist, currency = source(ticker)
            if len(hist) >= 50:
                break
            errors.append(f"{name}: only {len(hist)} days of prices")
        except Exception as e:
            errors.append(f"{name}: {e.__class__.__name__} – {str(e)[:100]}")
    else:
        result["price_error"] = " | ".join(errors)
        print(f"[prices] {ticker} {result['price_error']}")
        return result

    ma = hist.rolling(50).mean()
    price, ma50 = float(hist.iloc[-1]), float(ma.iloc[-1])
    result.update({
        "price": price,
        "ma50": ma50,
        "trend": "up" if price > ma50 else "down",
        "change_pct": float(hist.iloc[-1] / hist.iloc[-2] - 1) * 100,
        "currency": currency,
        "history": pd.DataFrame({"Close": hist, "MA50": ma}),
    })
    return result


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
    news_errors = []
    articles = score_articles(get_news(ticker, news_errors))
    score = aggregate(articles)
    tech = price_trend(ticker)
    signal, reason = decide(score, len(articles), tech["trend"], require_trend)
    counts = {k: sum(a["label"] == k for a in articles) for k in ("positive", "neutral", "negative")}
    return {
        "ticker": ticker, "score": score, "signal": signal, "reason": reason,
        "headlines": len(articles), "counts": counts, "articles": articles,
        "news_errors": news_errors, **tech,
    }


if __name__ == "__main__":
    # Quick test from the terminal:  python signals.py
    for t in config.DEFAULT_TICKERS:
        r = analyse(t)
        print(f"{t:8} {r['signal']:5} score={r['score']:+.2f}  "
              f"headlines={r['headlines']}  {r['reason']}")
