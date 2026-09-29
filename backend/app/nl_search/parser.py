"""Parser: plain-language request -> SearchRequest, using a local Ollama model."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import date
from typing import Protocol

import httpx
from pydantic import ValidationError

from .models import RawParse, SearchRequest
from .prompts import RETRY_TEMPLATE, SYSTEM_PROMPT, USER_TEMPLATE
from .resolve import resolve

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:32b")
HOME_LOCATION = os.getenv("HOME_LOCATION", "Bromont, QC")


class ParseError(RuntimeError):
    """Raised when the model fails to produce valid output after the retry."""


class LLMClient(Protocol):
    def chat(self, messages: list[dict], schema: dict) -> str: ...


class OllamaClient:
    """Minimal Ollama /api/chat client with JSON-schema structured output."""

    def __init__(self, model: str = OLLAMA_MODEL, url: str = OLLAMA_URL, timeout: float = 120.0):
        self.model = model
        self.url = url.rstrip("/")
        self.timeout = timeout

    def chat(self, messages: list[dict], schema: dict) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "format": schema,        # Ollama >= 0.5 constrains output to this schema
            "stream": False,
            "options": {"temperature": 0, "num_ctx": 4096},
        }
        resp = httpx.post(f"{self.url}/api/chat", json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()["message"]["content"]


@dataclass
class ParseResult:
    request: SearchRequest
    raw: RawParse
    attempts: int
    seconds: float
    missing: list[str] = field(default_factory=list)


def parse_request(text: str, client: LLMClient | None = None, today: date | None = None,
                  home_location: str = HOME_LOCATION) -> ParseResult:
    """Parse one request. Retries once, feeding the validation error back to the model."""
    client = client or OllamaClient()
    today = today or date.today()
    schema = RawParse.llm_schema()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_TEMPLATE.format(text=text)},
    ]
    start = time.perf_counter()
    last_error = ""

    for attempt in (1, 2):
        content = client.chat(messages, schema)
        try:
            raw = RawParse.model_validate(json.loads(content))
            request = resolve(raw, today=today, home_location=home_location)
            return ParseResult(request, raw, attempt, time.perf_counter() - start,
                               request.missing_fields())
        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            last_error = str(exc).splitlines()[0][:300]
            messages = messages[:2] + [
                {"role": "assistant", "content": content},
                {"role": "user", "content": RETRY_TEMPLATE.format(error=last_error, text=text)},
            ]

    raise ParseError(f"Could not parse request after 2 attempts: {last_error}")


if __name__ == "__main__":  # quick manual check: python -m nl_search.parser "your request"
    import sys

    query = " ".join(sys.argv[1:]) or "Adults-only all-inclusive, 7 nights in February, under $3000 for two"
    result = parse_request(query)
    print(result.request.model_dump_json(indent=2, exclude_none=True))
    print(f"\nattempts={result.attempts}  time={result.seconds:.1f}s  missing={result.missing}")
