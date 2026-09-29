"""Compare a parsed SearchRequest against a test case's expectations."""
from __future__ import annotations

import unicodedata
from typing import Any

from .models import SearchRequest


def _fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text))
    return "".join(c for c in text if not unicodedata.combining(c)).lower().strip()


def _as_json(value: Any) -> Any:
    return value.isoformat() if hasattr(value, "isoformat") else value


def compare(request: SearchRequest, expect: dict) -> list[str]:
    """Return a list of mismatch messages (empty list = pass)."""
    got = request.model_dump()
    errors: list[str] = []

    for key, want in expect.items():
        if key == "destinations":
            have = [_fold(d) for d in request.destinations]
            for name in want:
                if not any(_fold(name) in d or d in _fold(name) for d in have if d):
                    errors.append(f"destinations: expected '{name}' in {request.destinations}")
        elif key == "origin_airports":
            have = set(request.origin_airports or [])
            if have != set(want):
                errors.append(f"origin_airports: expected {sorted(want)}, got {sorted(have)}")
        elif key == "preferences_contains":
            joined = " | ".join(_fold(p) for p in request.preferences)
            for word in want:
                if _fold(word) not in joined:
                    errors.append(f"preferences: expected '{word}' in {request.preferences}")
        elif key == "missing":
            if set(request.missing_fields()) != set(want):
                errors.append(f"missing: expected {sorted(want)}, got {sorted(request.missing_fields())}")
        elif key == "children_ages":
            if sorted(request.children_ages) != sorted(want):
                errors.append(f"children_ages: expected {want}, got {request.children_ages}")
        else:
            have = _as_json(got.get(key))
            if isinstance(want, (int, float)) and isinstance(have, (int, float)):
                ok = abs(float(want) - float(have)) < 1e-6
            else:
                ok = have == want
            if not ok:
                errors.append(f"{key}: expected {want!r}, got {have!r}")
    return errors
