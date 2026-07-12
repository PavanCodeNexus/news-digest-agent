"""
Wall Street Journal fetcher.

WSJ publishes free public RSS feeds for headlines + short snippets
(full articles are paywalled, but we only ever use the short snippet
anyway — same as our other sources).
"""

import feedparser
from config import MAX_ARTICLES_PER_SOURCE
from fetchers import make_article

WSJ_FEEDS = {
    "World": "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    "Business & Economy": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
}


def _extract_rss_image(entry):
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url")
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get("type", "").startswith("image"):
                return enc.get("href") or enc.get("url")
    return None


def fetch_wsj():
    articles = []
    for category, url in WSJ_FEEDS.items():
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"[WSJ] Error fetching '{category}' RSS: {e}")
            continue

        if feed.bozo:
            print(f"[WSJ] Warning: feed parsing issue for '{category}' ({feed.bozo_exception})")

        for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE // 2]:
            articles.append(
                make_article(
                    title=entry.get("title"),
                    description=entry.get("summary"),
                    url=entry.get("link"),
                    source="The Wall Street Journal",
                    published_at=entry.get("published", ""),
                    category=category.lower(),
                    image_url=_extract_rss_image(entry),
                )
            )
    return articles
