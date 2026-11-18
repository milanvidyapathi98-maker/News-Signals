"""Step 1 – Collect recent news headlines for a ticker."""

from datetime import datetime, timedelta, timezone

import requests
import yfinance as yf

import config


def _from_yfinance(ticker: str) -> list[dict]:
    """Yahoo Finance news via yfinance (no API key needed)."""
    items = yf.Ticker(ticker).news or []
    articles = []
    for it in items:
        content = it.get("content", it)  # newer yfinance nests data under "content"
        title = content.get("title")
        if not title:
            continue

        # Publish time: new format = ISO string, old format = unix timestamp
        if content.get("pubDate"):
            published = datetime.fromisoformat(content["pubDate"].replace("Z", "+00:00"))
        elif it.get("providerPublishTime"):
            published = datetime.fromtimestamp(it["providerPublishTime"], tz=timezone.utc)
        else:
            continue

        provider = content.get("provider") or {}
        url = (content.get("canonicalUrl") or {}).get("url") or it.get("link", "")
        articles.append({
            "title": title.strip(),
            "summary": (content.get("summary") or "").strip(),
            "source": provider.get("displayName") or it.get("publisher", "Yahoo"),
            "url": url,
            "published": published,
        })
    return articles


def _from_finnhub(ticker: str) -> list[dict]:
    """Finnhub company news (needs free API key; works best for US tickers)."""
    if not config.FINNHUB_API_KEY:
        return []
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=config.LOOKBACK_DAYS)
    resp = requests.get(
        "https://finnhub.io/api/v1/company-news",
        params={"symbol": ticker, "from": start.isoformat(), "to": today.isoformat(),
                "token": config.FINNHUB_API_KEY},
        timeout=15,
    )
    if resp.status_code != 200:
        return []
    return [{
        "title": a.get("headline", "").strip(),
        "summary": (a.get("summary") or "").strip(),
        "source": a.get("source", "Finnhub"),
        "url": a.get("url", ""),
        "published": datetime.fromtimestamp(a["datetime"], tz=timezone.utc),
    } for a in resp.json() if a.get("headline") and a.get("datetime")]


def get_news(ticker: str) -> list[dict]:
    """Combine sources, drop old and duplicate headlines, newest first."""
    articles = []
    for source in (_from_yfinance, _from_finnhub):
        try:
            articles += source(ticker)
        except Exception as e:  # one source failing shouldn't stop the program
            print(f"[news] {source.__name__} failed for {ticker}: {e}")

    cutoff = datetime.now(timezone.utc) - timedelta(days=config.LOOKBACK_DAYS)
    seen, unique = set(), []
    for a in sorted(articles, key=lambda x: x["published"], reverse=True):
        key = a["title"].lower()[:80]
        if a["published"] >= cutoff and key not in seen:
            seen.add(key)
            unique.append(a)
    return unique[: config.MAX_HEADLINES]
