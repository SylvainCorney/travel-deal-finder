"""Natural-language search endpoints.

POST /api/v1/nl-search/parse   plain-language request -> structured criteria,
                               one clarifying question if something is missing,
                               and a payload the existing /search/search endpoint accepts.
GET  /api/v1/nl-search/status  is the local Ollama model reachable and installed?
"""
from __future__ import annotations

from datetime import date, timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.core.config import settings
from app.nl_search import LLMClient, OllamaClient, ParseError, SearchRequest, parse_request

router = APIRouter()

# trip_type -> "sources" values understood by the existing search endpoint
LEGACY_SOURCES = {
    "all_inclusive": ["all_inclusive"],
    "flight_hotel": ["packages"],
    "flight_only": ["flights"],
    "hotel_only": ["hotels"],
}

QUESTIONS = {
    "dates": {
        "en": "When would you like to leave, and for how many nights?",
        "fr": "Quand aimeriez-vous partir, et pour combien de nuits?",
    },
    "nights": {
        "en": "How many nights would you like to stay?",
        "fr": "Combien de nuits souhaitez-vous rester?",
    },
    "trip_type": {
        "en": "What are you looking for: all-inclusive, flight + hotel, flight only, or hotel only?",
        "fr": "Que recherchez-vous : tout inclus, vol + hôtel, vol seulement ou hôtel seulement?",
    },
}


# --- dependencies (overridable in tests) --------------------------------------

def get_llm_client() -> LLMClient:
    return OllamaClient(model=settings.OLLAMA_MODEL, url=settings.OLLAMA_URL)


def get_today() -> date:
    return date.today()


# --- request / response models ---------------------------------------------------

class ParseBody(BaseModel):
    text: str = Field(..., min_length=3, max_length=1000)


class ParseResponse(BaseModel):
    request: SearchRequest
    missing: list[str]
    question: str | None = None            # Phase 2: one clarifying question
    warnings: list[str]
    legacy_search: dict | None = None      # ready for POST /search/search
    legacy_note: str | None = None
    attempts: int
    seconds: float


# --- helpers ----------------------------------------------------------------------

def clarifying_question(missing: list[str], language: str) -> str | None:
    """Ask about one thing at a time; dates first (the question also covers nights)."""
    for field in ("dates", "nights", "trip_type"):
        if field in missing:
            return QUESTIONS[field].get(language, QUESTIONS[field]["en"])
    return None


def to_legacy_search(req: SearchRequest) -> tuple[dict | None, str | None]:
    """Map to the current single-origin, single-destination search form.

    Until the multi-airport expander (Phase 3-4) exists, this uses the first
    origin, the first destination and the first date of the travel window.
    """
    if req.missing_fields():
        return None, None
    if not req.destinations:
        return None, "Add a destination to run a search (\"anywhere warm\" comes with the expander phase)."
    if not req.nights_min:
        return None, "Add a return date or number of nights to run a search."

    check_in = req.depart_earliest
    payload = {
        "origin": (req.origin_airports or [settings.DEFAULT_ORIGIN_AIRPORT])[0],
        "location": req.destinations[0],
        "check_in_date": check_in.isoformat(),
        "check_out_date": (check_in + timedelta(days=req.nights_min)).isoformat(),
        "hotels": [],
        "airlines": [],
        "sources": LEGACY_SOURCES[req.trip_type],
    }

    dropped = []
    if req.origin_airports and len(req.origin_airports) > 1:
        dropped.append(f"other airports ({', '.join(req.origin_airports[1:])})")
    if len(req.destinations) > 1:
        dropped.append(f"other destinations ({', '.join(req.destinations[1:])})")
    if req.depart_latest and req.depart_latest != req.depart_earliest:
        dropped.append(f"flexible dates up to {req.depart_latest.isoformat()}")
    if req.nights_max and req.nights_max != req.nights_min:
        dropped.append(f"stays up to {req.nights_max} nights")
    note = ("Current search uses the first option only; not yet searched: " + "; ".join(dropped)
            if dropped else None)
    return payload, note


# --- endpoints ---------------------------------------------------------------------

@router.post("/parse", response_model=ParseResponse)
async def parse(body: ParseBody,
                client: LLMClient = Depends(get_llm_client),
                today: date = Depends(get_today)) -> ParseResponse:
    try:
        result = await run_in_threadpool(
            lambda: parse_request(body.text, client=client, today=today,
                                  home_location=settings.HOME_LOCATION))
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503,
                            detail=f"Local AI model not reachable at {settings.OLLAMA_URL} ({exc}). "
                                   f"Is Ollama running?")
    except ParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    req = result.request
    legacy, note = to_legacy_search(req)
    return ParseResponse(
        request=req,
        missing=result.missing,
        question=clarifying_question(result.missing, req.language),
        warnings=req.warnings,
        legacy_search=legacy,
        legacy_note=note,
        attempts=result.attempts,
        seconds=round(result.seconds, 2),
    )


@router.get("/status")
async def status():
    try:
        async with httpx.AsyncClient(timeout=5) as http:
            tags = (await http.get(f"{settings.OLLAMA_URL}/api/tags")).json()
    except httpx.HTTPError as exc:
        return {"ollama": "unreachable", "url": settings.OLLAMA_URL, "error": str(exc)}
    names = {m["name"] for m in tags.get("models", [])}
    installed = settings.OLLAMA_MODEL in names or f"{settings.OLLAMA_MODEL}:latest" in names
    return {"ollama": "ok", "url": settings.OLLAMA_URL, "model": settings.OLLAMA_MODEL,
            "model_installed": installed}
