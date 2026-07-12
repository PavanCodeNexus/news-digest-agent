"""
Times of India fetcher — public RSS, no API key needed.
"""

import feedparser
from config import MAX_ARTICLES_PER_SOURCE
from fetchers import make_article

TOI_RSS_URL = "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"


def _extract_rss_image(entry):
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url")
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get("type", "").startswith("image"):
                return enc.get("href") or enc.get("url")
    return None


def fetch_toi():
    try:
        feed = feedparser.parse(TOI_RSS_URL)
    except Exception as e:
        print(f"[Times of India] Error fetching RSS: {e}")
        return []

    if feed.bozo:
        print(f"[Times of India] Warning: feed parsing issue ({feed.bozo_exception})")

    articles = []
    for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
        articles.append(
            make_article(
                title=entry.get("title"),
                description=entry.get("summary"),
                url=entry.get("link"),
                source="The Times of India",
                published_at=entry.get("published", ""),
                category="india",
                image_url=_extract_rss_image(entry),
            )
        )
    return articles
