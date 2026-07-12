"""
The Guardian Open Platform fetcher — good for international relations
and deeper global analysis. Free tier, no commercial-use restriction.
Docs: https://open-platform.theguardian.com/documentation/
"""

import requests
from config import GUARDIAN_API_KEY, MAX_ARTICLES_PER_SOURCE
from fetchers import make_article

BASE_URL = "https://content.guardianapis.com/search"


def fetch_guardian(section="world", query=None):
    """
    section options: world, politics, business, environment,
                      science, technology, society
    """
    if not GUARDIAN_API_KEY:
        print("[Guardian] Skipped — GUARDIAN_API_KEY not set.")
        return []

    params = {
        "api-key": GUARDIAN_API_KEY,
        "section": section,
        "order-by": "newest",
        "page-size": MAX_ARTICLES_PER_SOURCE,
        "show-fields": "trailText,thumbnail",  # trailText = summary, thumbnail = image URL
    }
    if query:
        params["q"] = query

    try:
        resp = requests.get(BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"[Guardian] Error fetching news: {e}")
        return []

    articles = []
    for item in data.get("response", {}).get("results", []):
        fields = item.get("fields", {})
        articles.append(
            make_article(
                title=item.get("webTitle"),
                description=fields.get("trailText", ""),
                url=item.get("webUrl"),
                source="The Guardian",
                published_at=item.get("webPublicationDate"),
                category=section,
                image_url=fields.get("thumbnail"),
            )
        )
    return articles
