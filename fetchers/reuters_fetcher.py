"""
Reuters fetcher.

Reuters discontinued its own public RSS feeds years ago, so we use
Google News' RSS search feature filtered to reuters.com articles —
a well-known, legitimate workaround (not scraping) that many news
tools use for this exact reason.
"""

import feedparser
from config import MAX_ARTICLES_PER_SOURCE
from fetchers import make_article

REUTERS_GOOGLE_NEWS_URL = (
    "https://news.google.com/rss/search?q=when:24h+allinurl:reuters.com"
    "&ceid=US:en&hl=en-US&gl=US"
)


def _extract_rss_image(entry):
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url")
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get("type", "").startswith("image"):
                return enc.get("href") or enc.get("url")
    return None


def fetch_reuters():
    try:
        feed = feedparser.parse(REUTERS_GOOGLE_NEWS_URL)
    except Exception as e:
        print(f"[Reuters] Error fetching RSS: {e}")
        return []

    if feed.bozo:
        print(f"[Reuters] Warning: feed parsing issue ({feed.bozo_exception})")

    articles = []
    for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
        articles.append(
            make_article(
                title=entry.get("title"),
                description=entry.get("summary"),
                url=entry.get("link"),
                source="Reuters",
                published_at=entry.get("published", ""),
                category="world",
                image_url=_extract_rss_image(entry),
            )
        )
    return articles
