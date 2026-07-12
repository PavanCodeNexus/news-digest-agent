"""
PIB (Press Information Bureau) RSS fetcher — government schemes,
policy announcements, ministry releases. Arguably the single most
important source for UPSC's Polity & Governance coverage.

No API key needed — this is a public RSS feed.
"""

import feedparser
from config import PIB_RSS_URL, MAX_ARTICLES_PER_SOURCE
from fetchers import make_article


def _extract_rss_image(entry):
    """RSS feeds sometimes include an image via <media:thumbnail> or <enclosure>.
    Returns the image URL if found, otherwise None."""
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url")
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get("type", "").startswith("image"):
                return enc.get("href") or enc.get("url")
    return None


def fetch_pib():
    try:
        feed = feedparser.parse(PIB_RSS_URL)
    except Exception as e:
        print(f"[PIB] Error fetching RSS: {e}")
        return []

    if feed.bozo:
        # bozo=True means the feed had parsing issues, but feedparser
        # is lenient and often still extracts usable entries — so we
        # warn but don't necessarily bail out.
        print(f"[PIB] Warning: feed parsing issue ({feed.bozo_exception})")

    articles = []
    for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
        articles.append(
            make_article(
                title=entry.get("title"),
                description=entry.get("summary"),
                url=entry.get("link"),
                source="PIB",
                published_at=entry.get("published", ""),
                category="governance",
                image_url=_extract_rss_image(entry),
            )
        )
    return articles
