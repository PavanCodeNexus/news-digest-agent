"""
The Hindu RSS fetcher — UPSC's most recommended newspaper.
No API key needed — public RSS feed.
"""

import feedparser
from config import HINDU_RSS_URL, MAX_ARTICLES_PER_SOURCE
from fetchers import make_article


def _extract_rss_image(entry):
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url")
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get("type", "").startswith("image"):
                return enc.get("href") or enc.get("url")
    return None


def fetch_hindu():
    try:
        feed = feedparser.parse(HINDU_RSS_URL)
    except Exception as e:
        print(f"[The Hindu] Error fetching RSS: {e}")
        return []

    if feed.bozo:
        print(f"[The Hindu] Warning: feed parsing issue ({feed.bozo_exception})")

    articles = []
    for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
        articles.append(
            make_article(
                title=entry.get("title"),
                description=entry.get("summary"),
                url=entry.get("link"),
                source="The Hindu",
                published_at=entry.get("published", ""),
                category="national",
                image_url=_extract_rss_image(entry),
            )
        )
    return articles
