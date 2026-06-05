"""Discord communication helpers."""

from typing import Any, Optional
import requests
from .config import AppConfig


# Configured by main at startup (module-private storage)
_discord_webhook_url: Optional[str] = None
_discord_channel_id: Optional[int] = None


def configure(cfg: AppConfig) -> None:
    """Configure the Discord webhook URL and channel id from AppConfig."""
    global _discord_webhook_url, _discord_channel_id
    _discord_webhook_url = cfg.discord_webhook_url
    _discord_channel_id = int(cfg.discord_channel_id)


def send_embed(
    title: str,
    url: str,
    score: int,
    story_id: Any,
    source: str = "Hacker News",
    accept_reason: Optional[str] = None,
    summary: Optional[str] = None,
) -> None:
    """Send an embed payload to the configured Discord webhook URL."""
    if not _discord_webhook_url:
        raise RuntimeError("Discord webhook URL is not configured")
    embed: dict[str, Any] = {
        "title": title,
        "url": url,
        "color": 3066993,
        "footer": {"text": f"Source: {source} • ID: {story_id} • Score: {score}"},
        "author": {"name": "Felinobot"},
    }
    description_parts: list[str] = []
    if accept_reason:
        description_parts.append(f"Why it matched: {accept_reason}")
    if summary:
        description_parts.append(f"Summary: {summary}")
    if description_parts:
        embed["description"] = "\n\n".join(description_parts)
    resp = requests.post(_discord_webhook_url, json={"embeds": [embed]})
    resp.raise_for_status()
