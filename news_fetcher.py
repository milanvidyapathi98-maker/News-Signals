"""Step 1 – Collect recent news headlines for a ticker."""

import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import requests
import yfinance as yf

import config

HEADERS = {"User-Agent": "Mozilla/5.0 (NewsSignal research app)"}
NAME_BY_TICKER = {t: n for n, t in config.COMPANIES.items()}


def _from_yfinance(ticker: str) -> list[dict]:
    """Yahoo Finance news via yfinance (no API key needed)."""
    tk = yf.Ticker(ticker)
    try:
        items = tk.get_news(count=config.MAX_HEADLINES) or []
    except (AttributeError, TypeError):  # older yfinance versions
        items = tk.news or []

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
        url = ((content.get("canonicalUrl") or {}).get("url")
               or (content.get("clickThroughUrl") or {}).get("url") or it.get("link", ""))
        articles.append({
            "title": title.strip(),
            "summary": (content.get("summary") or "").strip(),
            "source": provider.get("displayName") or it.get("publisher", "Yahoo Finance"),
            "url": url,
            "published": published,
        })
    return articles


def _from_google_news(ticker: str) -> list[dict]:
    """Google News RSS search (no API key needed). Searches by company name."""
    name = NAME_BY_TICKER.get(ticker, ticker)
    name = name.split(" (")[0]  # "Alphabet (Google)" -> "Alphabet"
    query = quote_plus(f'"{name}" stock when:{config.LOOKBACK_DAYS}d')
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()

    articles = []
    for item in ET.fromstring(resp.content).iter("item"):
        title = (item.findtext("title") or "").strip()
        pub = item.findtext("pubDate")
        if not title or not pub:
            continue
        source = (item.findtext("source") or "Google News").strip()
        # Google adds " - Source" at the end of the title; remove it
        if title.endswith(" - " + source):
            title = title[: -len(" - " + source)]
        articles.append({
            "title": title,
            "summary": "",
            "source": source,
            "url": item.findtext("link") or "",
            "published": parsedate_to_datetime(pub).astimezone(timezone.utc),
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
    resp.raise_for_status()
    return [{
        "title": a.get("headline", "").strip(),
        "summary": (a.get("summary") or "").strip(),
        "source": a.get("source", "Finnhub"),
        "url": a.get("url", ""),
        "published": datetime.fromtimestamp(a["datetime"], tz=timezone.utc),
    } for a in resp.json() if a.get("headline") and a.get("datetime")]


SOURCES = {
    "Yahoo Finance": _from_yfinance,
    "Google News": _from_google_news,
    "Finnhub": _from_finnhub,
}


def get_news(ticker: str, errors: list | None = None) -> list[dict]:
    """Combine all sources, drop old and duplicate headlines, newest first.

    If a source fails, a short message is added to `errors` (shown in the app).
    """
    articles = []
    for name, source in SOURCES.items():
        try:
            articles += source(ticker)
        except Exception as e:  # one source failing shouldn't stop the program
            msg = f"{name}: {e.__class__.__name__} – {str(e)[:120]}"
            print(f"[news] {ticker} {msg}")
            if errors is not None:
                errors.append(msg)

    cutoff = datetime.now(timezone.utc) - timedelta(days=config.LOOKBACK_DAYS)
    seen, unique = set(), []
    for a in sorted(articles, key=lambda x: x["published"], reverse=True):
        key = "".join(ch for ch in a["title"].lower() if ch.isalnum())[:70]
        if a["published"] >= cutoff and key not in seen:
            seen.add(key)
            unique.append(a)
    return unique[: config.MAX_HEADLINES]


if __name__ == "__main__":
    # Quick test:  python news_fetcher.py
    for t in config.DEFAULT_TICKERS:
        errs = []
        news = get_news(t, errs)
        print(f"{t:8} {len(news):3} headlines", "| errors:", errs or "none")