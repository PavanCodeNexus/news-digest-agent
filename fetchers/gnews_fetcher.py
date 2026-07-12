"""
GNews.io fetcher — general world/breaking news.
Docs: https://gnews.io/docs/v4
"""

import requests
from config import GNEWS_API_KEY, MAX_ARTICLES_PER_SOURCE
from fetchers import make_article

BASE_URL = "https://gnews.io/api/v4/top-headlines"


def fetch_gnews(category="world", country="in", lang="en"):
    """
    category options: general, world, nation, business, technology,
                       entertainment, sports, science, health
    """
    if not GNEWS_API_KEY:
        print("[GNews] Skipped — GNEWS_API_KEY not set.")
        return []

    params = {
        "token": GNEWS_API_KEY,
        "lang": lang,
        "country": country,
        "category": category,
        "max": MAX_ARTICLES_PER_SOURCE,
    }

    try:
        resp = requests.get(BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"[GNews] Error fetching news: {e}")
        return []

    articles = []
    for item in data.get("articles", []):
        articles.append(
            make_article(
                title=item.get("title"),
                description=item.get("description"),
                url=item.get("url"),
                source=item.get("source", {}).get("name", "GNews"),
                published_at=item.get("publishedAt"),
                category=category,
                image_url=item.get("image"),
            )
        )
    return articles
