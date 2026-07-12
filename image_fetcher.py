"""
Fetches a relevant stock photo for a given search term using the Pexels API
(free, no cost). Used to give each poster headline a real, relevant image
instead of plain text.
"""

import io
import requests
from PIL import Image, ImageOps
from config import PEXELS_API_KEY

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"

# Simple in-memory cache so we don't re-fetch the same category image
# multiple times in one run.
_image_cache = {}


def fetch_image_from_url(image_url, size=(340, 190)):
    """
    Downloads the actual image published by the news source itself.
    Returns a cropped/resized PIL Image, or None if it fails for any reason.
    """
    if not image_url:
        return None

    cache_key = ("url", image_url, size)
    if cache_key in _image_cache:
        return _image_cache[cache_key]

    headers = {
        # Some news sites reject requests that don't look like a browser
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
    }

    try:
        resp = requests.get(image_url, headers=headers, timeout=20)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        img = ImageOps.fit(img, size, method=Image.LANCZOS)
        _image_cache[cache_key] = img
        return img
    except (requests.RequestException, OSError) as e:
        print(f"[ImageFetcher] Could not download article image: {e}")
        return None


def fetch_image_for_query(query, size=(360, 280)):
    """
    Returns a PIL Image cropped/resized to `size`, or None if unavailable
    (missing key, network issue, no results) — callers should handle None
    by falling back to a plain placeholder box.
    """
    if not PEXELS_API_KEY:
        return None

    cache_key = (query, size)
    if cache_key in _image_cache:
        return _image_cache[cache_key]

    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query, "per_page": 1, "orientation": "landscape"}

    try:
        resp = requests.get(PEXELS_SEARCH_URL, headers=headers, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        photos = data.get("photos", [])
        if not photos:
            return None

        image_url = photos[0]["src"]["large"]
        img_resp = requests.get(image_url, timeout=20)
        img_resp.raise_for_status()

        img = Image.open(io.BytesIO(img_resp.content)).convert("RGB")
        # Center-crop + resize to exactly fill the target box (no distortion)
        img = ImageOps.fit(img, size, method=Image.LANCZOS)

        _image_cache[cache_key] = img
        return img

    except (requests.RequestException, KeyError, IndexError, OSError) as e:
        print(f"[Pexels] Could not fetch image for '{query}': {e}")
        return None
