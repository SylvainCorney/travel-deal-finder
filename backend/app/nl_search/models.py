"""Data models for Phase 1: natural-language parsing.

Two layers:
  RawParse       - what the LLM returns. Only language extraction: no date math,
                   no budget math. Every field nullable so the LLM never has to guess.
  SearchRequest  - what the rest of the pipeline uses. Built by resolve.py with
                   deterministic Python (dates, nights, total budget, airport codes).
"""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

TripType = Literal["all_inclusive", "flight_hotel", "flight_only", "hotel_only"]


class RawParse(BaseModel):
    """LLM output. Mirrors the JSON schema sent to Ollama.

    Field ORDER matters: with a JSON schema, Ollama writes fields in this order, so
    it follows how people describe a trip (what, who, from, to, when, extras).
    """

    language: Literal["en", "fr"] = "en"
    trip_type: TripType | None = None

    # Who
    adults: int | None = Field(None, ge=1, le=12)
    children_ages: list[int] = Field(default_factory=list)
    adults_only_resort: bool | None = None

    # From / to
    origin_airports: list[str] = Field(default_factory=list)  # as written; resolve.py maps to codes
    destinations: list[str] = Field(default_factory=list)
    max_drive_hours: float | None = Field(None, ge=0, le=24)

    # When - raw parts only; Python resolves them into real dates
    depart_month: int | None = Field(None, ge=1, le=12)
    depart_day: int | None = Field(None, ge=1, le=31)
    depart_year: int | None = None
    window_end_month: int | None = Field(None, ge=1, le=12)
    window_end_day: int | None = Field(None, ge=1, le=31)
    flex_days: int | None = Field(None, ge=0, le=30)
    return_month: int | None = Field(None, ge=1, le=12)
    return_day: int | None = Field(None, ge=1, le=31)
    nights_min: int | None = Field(None, ge=1, le=60)
    nights_max: int | None = Field(None, ge=1, le=60)

    # Extras
    min_stars: float | None = Field(None, ge=1, le=5)
    direct_flight_only: bool | None = None
    budget_amount: float | None = Field(None, gt=0)
    budget_per_person: bool | None = None
    preferences: list[str] = Field(default_factory=list)

    @classmethod
    def llm_schema(cls) -> dict:
        """Schema sent to Ollama: EVERY field is required (null allowed), so the model
        cannot skip a field; it must write each one, in order, even if only null."""
        schema = cls.model_json_schema()
        schema["required"] = list(schema["properties"])
        return schema


class SearchRequest(BaseModel):
    """Resolved request used by the expander, scrapers and ranker (Phase 3+)."""

    # Who
    adults: int = 2
    children_ages: list[int] = Field(default_factory=list)
    adults_only_resort: bool | None = None

    # Where
    home_location: str
    destinations: list[str] = Field(default_factory=list)   # empty = "anywhere warm"
    origin_airports: list[str] | None = None               # None = auto by drive time
    max_drive_hours: float = 5.0

    # When (optional here so Phase 2 can ask a clarifying question)
    depart_earliest: date | None = None
    depart_latest: date | None = None
    nights_min: int | None = None
    nights_max: int | None = None

    # What
    trip_type: TripType | None = None
    min_stars: float | None = None
    direct_flight_only: bool = False
    max_budget_total_cad: float | None = None

    # Soft
    preferences: list[str] = Field(default_factory=list)
    language: Literal["en", "fr"] = "en"

    # Diagnostics (not used for searching)
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_ranges(self) -> "SearchRequest":
        if self.depart_earliest and self.depart_latest and self.depart_earliest > self.depart_latest:
            raise ValueError("depart_earliest is after depart_latest")
        if self.nights_min and self.nights_max and self.nights_min > self.nights_max:
            raise ValueError("nights_min is greater than nights_max")
        if self.min_stars is not None and (self.min_stars * 2) % 1:
            raise ValueError("min_stars must be in half-star steps")
        return self

    def missing_fields(self) -> list[str]:
        """Fields required before a search can run (drives Phase 2 clarification)."""
        missing = []
        if self.depart_earliest is None:
            missing.append("dates")
        if self.nights_min is None and self.trip_type != "flight_only":
            missing.append("nights")
        if self.trip_type is None:
            missing.append("trip_type")
        return missing

    @property
    def travellers(self) -> int:
        return self.adults + len(self.children_ages)
