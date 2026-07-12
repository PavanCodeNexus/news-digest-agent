"""
Phase 1: News Collection Agent
Pulls articles from all four sources, normalizes them, and prints
a combined summary. This is the foundation Phase 2 (LLM summarization)
will build on.

Run:
    python main.py
"""

from fetchers.gnews_fetcher import fetch_gnews
from fetchers.guardian_fetcher import fetch_guardian
from fetchers.pib_fetcher import fetch_pib
from fetchers.hindu_fetcher import fetch_hindu
from fetchers.reuters_fetcher import fetch_reuters
from fetchers.wsj_fetcher import fetch_wsj
from fetchers.toi_fetcher import fetch_toi
from fetchers.indianexpress_fetcher import fetch_indian_express
from summarizer import classify_and_summarize
from poster_generator import generate_important_digest, generate_full_digest
from notifier import send_critical_alert


def collect_all_news():
    all_articles = []

    print("Fetching from GNews...")
    all_articles.extend(fetch_gnews(category="world"))

    print("Fetching from The Guardian...")
    all_articles.extend(fetch_guardian(section="world"))

    print("Fetching from PIB...")
    all_articles.extend(fetch_pib())

    print("Fetching from The Hindu...")
    all_articles.extend(fetch_hindu())

    print("Fetching from Reuters...")
    all_articles.extend(fetch_reuters())

    print("Fetching from The Wall Street Journal...")
    all_articles.extend(fetch_wsj())

    print("Fetching from The Times of India...")
    all_articles.extend(fetch_toi())

    print("Fetching from The Indian Express...")
    all_articles.extend(fetch_indian_express())

    return all_articles


def print_by_importance(articles):
    """
    Groups articles by importance (Critical first), then by GS category.
    This is the most-important-first view.
    """
    order = {"Critical": 0, "Important": 1, "Routine": 2}
    sorted_articles = sorted(articles, key=lambda a: order.get(a.get("importance", "Routine"), 3))

    print(f"\n{'='*70}")
    print(f"DAILY CURRENT AFFAIRS DIGEST — {len(articles)} articles")
    print(f"{'='*70}\n")

    for a in sorted_articles:
        importance = a.get("importance", "Routine")
        category = a.get("category", "Miscellaneous")
        summary = a.get("ai_summary", "")
        tag = f"[{importance.upper()}] [{category}]"
        print(f"{tag}\n{a['title']}")
        if summary:
            print(f"  → {summary}")
        print(f"  Source: {a['source']}\n")


if __name__ == "__main__":
    articles = collect_all_news()
    print(f"\nSummarizing and classifying {len(articles)} articles with Gemini...")
    articles = classify_and_summarize(articles)
    print_by_importance(articles)
    send_critical_alert(articles)
    generate_important_digest(articles)
    generate_full_digest(articles)
