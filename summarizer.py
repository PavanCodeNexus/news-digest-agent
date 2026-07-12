"""
Phase 2 (v2): Summarization & Classification Agent — Groq version

Takes raw articles (from fetchers/) and uses Groq's free API (running
Llama 3.3 70B) to:
  1. Assign a section category (World, India, Business & Economy, etc.)
  2. Assign an importance level (Critical / Important / Routine)
  3. Write a short 2-line summary

Why Groq instead of Gemini: Gemini's free tier has been unstable —
models get retired or capped at as few as 20 requests/day. Groq's free
tier gives 30 requests/minute and 1,000 requests/day, which is far more
reliable for a project that runs once (or a few times) per day.

Groq's API is OpenAI-compatible, so this uses a standard chat-completions
call via `requests` — no extra SDK needed.
"""

import json
import time
import requests
from config import GROQ_API_KEY, GROQ_MODEL

GS_CATEGORIES = [
    "World",
    "India",
    "Business & Economy",
    "Sports",
    "Technology",
    "Crime & Justice",
]

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_INSTRUCTION = f"""You are a current affairs assistant for competitive exam preparation. You will be given a
list of news articles (title + short description). For EACH article, decide:

1. "category": one of exactly these categories: {", ".join(GS_CATEGORIES)}
2. "importance": one of exactly "Critical", "Important", or "Routine"
   - Critical = major policy/international/economic event that should not be missed today
   - Important = relevant background/current affairs, worth knowing
   - Routine = minor or low relevance
3. "summary": a crisp 2-line summary in your own words, written in a neutral,
   factual current-affairs style (no sensationalism).

Respond with ONLY a valid JSON object of this exact shape, no other text:
{{"results": [{{"index": 0, "category": "...", "importance": "...", "summary": "..."}}, ...]}}
The "index" must match the position of the article in the input list (starting at 0).
"""


def _classify_batch(batch_articles, start_index):
    """Sends one batch of articles to Groq and returns results keyed by original index."""
    input_for_model = [
        {"index": start_index + i, "title": a["title"], "description": a["description"]}
        for i, a in enumerate(batch_articles)
    ]

    user_prompt = (
        "Classify and summarize these articles:\n\n"
        + json.dumps(input_for_model, ensure_ascii=False)
    )

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    data = None
    last_error = None
    retry_delays = [5, 15]  # Groq's limits are generous, so short waits are enough
    for attempt in range(1, 3):
        try:
            resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            break
        except requests.RequestException as e:
            last_error = e
            error_detail = ""
            if e.response is not None:
                try:
                    error_detail = f" | Details: {e.response.json()}"
                except Exception:
                    error_detail = f" | Raw: {e.response.text[:300]}"
            print(f"[Summarizer] Batch starting at {start_index}, attempt {attempt} failed: {e}{error_detail}")
            if attempt < 2:
                wait = retry_delays[attempt - 1]
                print(f"[Summarizer] Waiting {wait}s before retrying...")
                time.sleep(wait)

    if data is None:
        print(f"[Summarizer] Batch starting at {start_index} failed after retries: {last_error}")
        return {}

    try:
        raw_text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        print(f"[Summarizer] Unexpected response shape: {e}")
        return {}

    try:
        parsed = json.loads(raw_text)
        results = parsed.get("results", [])
    except json.JSONDecodeError as e:
        print(f"[Summarizer] Failed to parse model output as JSON: {e}")
        return {}

    return {r["index"]: r for r in results if "index" in r}


def classify_and_summarize(articles, batch_size=15):
    """
    Takes a list of normalized article dicts (from fetchers) and returns
    the same list with 'category', 'importance', and 'ai_summary' fields added.

    Groq's free tier (30 RPM / 1,000 RPD) comfortably handles a few
    batches per run, so no long artificial delays are needed here.
    """
    if not GROQ_API_KEY:
        print("[Summarizer] Skipped — GROQ_API_KEY not set.")
        return articles

    if not articles:
        return articles

    results_by_index = {}
    num_batches = -(-len(articles) // batch_size)  # ceiling division
    for batch_num, start in enumerate(range(0, len(articles), batch_size), start=1):
        batch = articles[start:start + batch_size]
        print(f"[Summarizer] Processing articles {start+1}-{start+len(batch)} of {len(articles)}...")
        batch_results = _classify_batch(batch, start)
        results_by_index.update(batch_results)

        if batch_num < num_batches:
            time.sleep(2)  # small courtesy pause between batches

    for i, article in enumerate(articles):
        result = results_by_index.get(i)
        if result:
            article["category"] = result.get("category", "Miscellaneous")
            article["importance"] = result.get("importance", "Routine")
            article["ai_summary"] = result.get("summary", "")
        else:
            article["importance"] = "Routine"
            article["ai_summary"] = ""

    return articles
