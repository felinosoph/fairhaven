"""Environment helpers for reading and validating environment variables.

This module contains simple helpers used by `main.py` to read required
configuration values from the environment. `load_dotenv()` should be
called by the application entrypoint (typically `main.py`) before using
these helpers.
"""

from typing import Optional
import os
from dataclasses import dataclass


@dataclass
class AppConfig:
    """Application configuration container built from environment variables."""

    discord_webhook_url: str
    discord_channel_id: int
    upstash_url: str
    upstash_token: str
    openai_api_key: str
    hn_prompt_path: Optional[str] = None
    arxiv_prompt_path: Optional[str] = None
    prompt_path: Optional[str] = None


def read_env_str(
    name: str, default: Optional[str] = None, required: bool = True
) -> str:
    """Read an environment variable as a string.

    Args:
        name: Environment variable name.
        default: Value to return when the variable is not set and not required.
        required: If True, raise EnvironmentError when missing or empty.

    Returns:
        The environment variable value as a string.

    Raises:
        EnvironmentError: if required is True and the variable is missing/empty.
    """
    val = os.getenv(name, default)
    if required and (val is None or val == ""):
        raise EnvironmentError(f"Required environment variable {name} is not set")
    return val  # type: ignore[return-value]


def read_env_int(
    name: str, default: Optional[int] = None, required: bool = True
) -> int:
    """Read an environment variable and parse it as an integer.

    Args:
        name: Environment variable name.
        default: Value to return when missing and not required.
        required: If True, raise EnvironmentError when missing or unparsable.

    Returns:
        The parsed integer value.

    Raises:
        EnvironmentError: if required is True and missing or cannot be parsed as int.
    """
    raw = os.getenv(name)
    if raw is None or raw == "":
        if default is not None:
            return default
        if required:
            raise EnvironmentError(f"Required environment variable {name} is not set")
        raise EnvironmentError(
            f"Environment variable {name} is not set and no default provided"
        )
    try:
        return int(raw)
    except ValueError:
        raise EnvironmentError(
            f"Environment variable {name} must be an integer, got: {raw}"
        )


def build_config() -> AppConfig:
    """Build an AppConfig from environment variables.

    Calls the read_env_* helpers and constructs an `AppConfig` instance.
    """
    discord_webhook = read_env_str("DISCORD_WEBHOOK_URL")
    discord_channel = read_env_int("DISCORD_CHANNEL_ID")
    upstash_url = read_env_str("UPSTASH_REDIS_URL")
    upstash_token = read_env_str("UPSTASH_REDIS_TOKEN")
    openai_key = read_env_str("OPENAI_API_KEY")
    hn_prompt_path = read_env_str(
        "HN_FILTER_PROMPT_FILE", default="prompt_example.txt", required=False
    )
    arxiv_prompt_path = read_env_str(
        "ARXIV_FILTER_PROMPT_FILE", default="arxiv_prompt.txt", required=False
    )
    return AppConfig(
        discord_webhook_url=discord_webhook,
        discord_channel_id=discord_channel,
        upstash_url=upstash_url,
        upstash_token=upstash_token,
        openai_api_key=openai_key,
        hn_prompt_path=hn_prompt_path,
        arxiv_prompt_path=arxiv_prompt_path,
        prompt_path=hn_prompt_path,
    )
