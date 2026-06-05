"""OpenAI interaction wrapper."""

import json
from pathlib import Path
from string import Template
from typing import Optional, Tuple, Union

from openai import OpenAI

from .config import AppConfig

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_FILTER_PROMPT_FILE = Path("prompt_example.txt")

# OpenAI client must be configured by main.
client: Optional[OpenAI] = None
_prompt_path: Optional[Path] = None


def configure(cfg: AppConfig) -> None:
    """Configure the OpenAI client and optional prompt path from AppConfig."""
    global client, _prompt_path
    client = OpenAI(api_key=cfg.openai_api_key)

    prompt_path = cfg.prompt_path or str(DEFAULT_FILTER_PROMPT_FILE)
    candidate = Path(prompt_path)
    if candidate.is_absolute():
        _prompt_path = candidate
    else:
        # Resolve relative prompt paths from the repository root.
        _prompt_path = (BASE_DIR.parent / candidate).resolve()


def _load_prompt_from_file(path: Union[Path, str]) -> str:
    """Load the first readable prompt template from known locations."""
    candidates: list[Path] = []

    if _prompt_path is not None:
        candidates.append(_prompt_path)

    provided = Path(path) if not isinstance(path, Path) else path
    candidates.append(provided)
    candidates.append(BASE_DIR.parent / DEFAULT_FILTER_PROMPT_FILE)

    for candidate in candidates:
        try:
            if candidate.exists():
                return candidate.read_text(encoding="utf-8").strip()
        except Exception:
            continue

    return ""


def analyze_story(
    title: str, url: str, text: str = "", prompt_template: Optional[str] = None
) -> Tuple[bool, str, str, str]:
    """Return (interesting, accept_reason, reject_reason, summary).

    The function returns a 4-tuple:
      - interesting: True when the story matches the filter
      - accept_reason: explanation when interesting is True, else empty string
      - reject_reason: explanation when interesting is False, else empty string
      - summary: a concise two-sentence summary of the story
    """
    template = prompt_template or _load_prompt_from_file(DEFAULT_FILTER_PROMPT_FILE)
    # Ensure the model always has something to evaluate. If the item has no
    # `text` field (HN often omits it), fall back to using the title as the
    # content so the filter can still make a judgment.
    evaluated_text = text if (text and text.strip()) else title
    prompt = Template(template).safe_substitute(
        title=title, url=url, text=evaluated_text
    )
    if client is None:
        raise RuntimeError(
            "OpenAI client not configured. Call ai_client.configure(api_key) first."
        )

    try:
        # Add a system message that explicitly instructs the model to
        # return a JSON object. The OpenAI server requires the messages
        # to mention 'json' when using response_format type 'json_object'.
        system_msg = (
            "Evaluate the provided content and return a JSON object only. "
            "The object must follow this schema: "
            '{"interesting": true|false, "accept_reason": "why accept", "reject_reason": "why reject", "summary": "two-sentence summary"}.'
            " If the item has no body/text, use the title and url to decide."
        )
        response = client.chat.completions.create(
            model="gpt-5.4-nano",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        content = None
        try:
            content = getattr(response.choices[0].message, "content", None)
        except Exception:
            content = None
        if not content:
            return False, "", "", ""
        data = json.loads(content)
        interesting = bool(data.get("interesting", False))
        accept_reason = data.get("accept_reason") or data.get("reason") or ""
        reject_reason = data.get("reject_reason") or (
            "" if interesting else (data.get("reason") or "")
        )
        summary = data.get("summary") or ""
        if interesting:
            return True, str(accept_reason), "", str(summary)
        return False, "", str(reject_reason), str(summary)
    except Exception as e:
        # Surface the raw error for debugging and return a safe fallback.
        print(f"OpenAI filtering error: {e}")
        return False, "", "", ""
