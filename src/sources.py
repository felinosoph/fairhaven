"""News source fetchers (Hacker News for now)."""

import requests
from typing import Any, Optional


def fetch_json(url: str) -> Optional[Any]:
    """Fetch JSON from a URL using `requests` and return the decoded object, or None on error."""
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def fetch_hn_top_ids() -> Optional[list[int]]:
    """Return top story IDs from Hacker News, or None on error."""
    return fetch_json("https://hacker-news.firebaseio.com/v0/topstories.json")


def fetch_hn_item(story_id: int) -> Optional[dict[str, Any]]:
    """Fetch a Hacker News item by id and return its JSON dict, or None."""
    return fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
