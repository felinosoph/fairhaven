"""Storage helpers using Upstash Redis."""

from typing import Any, Optional
from .config import AppConfig

from upstash_redis import Redis


# Redis client must be configured by main
redis_client: Optional[Redis] = None

DEFAULT_TTL = 60 * 60 * 24 * 5


def configure(cfg: AppConfig) -> None:
    """Configure the Upstash Redis client using an AppConfig."""
    global redis_client
    redis_client = Redis(url=str(cfg.upstash_url), token=str(cfg.upstash_token))


def _ensure_configured() -> None:
    if redis_client is None:
        raise RuntimeError(
            "Redis client not configured. Call storage.configure(cfg) first."
        )


def is_processed(story_id: Any) -> bool:
    """Return True if the story id has been marked processed."""
    _ensure_configured()
    return bool(redis_client.exists(str(story_id)))


def mark_processed(story_id: Any, ttl: int = DEFAULT_TTL) -> None:
    """Mark a story id as processed with an expiry TTL (seconds)."""
    _ensure_configured()
    redis_client.setex(str(story_id), ttl, "1")


def get_filter_prompt() -> Optional[str]:
    """Return the filter prompt stored in Redis, or None if missing."""
    _ensure_configured()
    val = redis_client.get("filter_prompt")
    if not val:
        return None
    return val.decode() if isinstance(val, (bytes, bytearray)) else str(val)
