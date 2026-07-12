"""
Common normalized article schema used across all fetchers.
Every fetcher returns a list of dicts shaped like this, regardless
of the source's original format. This is what makes the pipeline
"pluggable" — Phase 2 (summarization) only needs to know this one shape.
"""


def make_article(title, description, url, source, published_at, category="general", image_url=None):
    return {
        "title": (title or "").strip(),
        "description": (description or "").strip(),
        "url": url or "",
        "source": source,
        "published_at": published_at or "",
        "category": category,
        "image_url": image_url,
    }
