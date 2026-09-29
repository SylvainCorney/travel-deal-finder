"""Deterministic resolution: RawParse (LLM output) -> SearchRequest.

All calendar, budget and airport-code logic lives here so it can be unit-tested
and never depends on the LLM doing arithmetic.
"""
from __future__ import annotations

import calendar
import unicodedata
from datetime import date, timedelta

from .models import RawParse, SearchRequest

# Airport catalog (Phase 3 will move this to config/airports.yaml with drive times)
AIRPORTS = {
    "YUL": "Montréal-Trudeau",
    "YHU": "Montréal Saint-Hubert",
    "YQB": "Québec City",
    "YOW": "Ottawa",
    "YYZ": "Toronto Pearson",
    "BTV": "Burlington, VT",
    "PBG": "Plattsburgh, NY",
    "BOS": "Boston Logan",
}

# City / nickname -> code, for when the LLM returns a name instead of a code
_CITY_TO_CODE = {
    "montreal": "YUL", "trudeau": "YUL", "dorval": "YUL",
    "saint-hubert": "YHU", "st-hubert": "YHU", "st hubert": "YHU",
    "quebec": "YQB", "quebec city": "YQB",
    "ottawa": "YOW",
    "toronto": "YYZ", "pearson": "YYZ",
    "burlington": "BTV",
    "plattsburgh": "PBG",
    "boston": "BOS", "logan": "BOS",
}


def _fold(text: str) -> str:
    """Lower-case and strip accents: 'Montréal' -> 'montreal'."""
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c)).lower().strip()


def normalize_airports(values: list[str]) -> tuple[list[str], list[str]]:
    """Map what the traveller wrote ("Montréal", "Boston Logan", "PBG") to codes.

    Returns (known codes, warnings). Order preserved, duplicates removed.
    Longer names are tried first so "Montréal Saint-Hubert" maps to YHU, not YUL.
    """
    names = sorted(_CITY_TO_CODE, key=len, reverse=True)
    codes, warnings = [], []
    for value in values:
        key = value.strip().upper()
        folded = _fold(value)
        code = key if key in AIRPORTS else next((_CITY_TO_CODE[n] for n in names if n in folded), None)
        if code is None:
            warnings.append(f"Unknown departure airport '{value}' ignored")
        elif code not in codes:
            codes.append(code)
    return codes, warnings


def _safe_date(year: int, month: int, day: int) -> date:
    """Clamp the day to the month length (e.g. Feb 30 -> Feb 28/29)."""
    return date(year, month, min(day, calendar.monthrange(year, month)[1]))


def _next_occurrence(month: int, day: int, today: date, year: int | None = None) -> date:
    """Explicit year wins; otherwise the next date on/after today."""
    if year:
        return _safe_date(year, month, day)
    candidate = _safe_date(today.year, month, day)
    return candidate if candidate >= today else _safe_date(today.year + 1, month, day)


def _on_or_after(month: int, day: int, anchor: date) -> date:
    """First date with this month/day on or after the anchor date."""
    candidate = _safe_date(anchor.year, month, day)
    return candidate if candidate >= anchor else _safe_date(anchor.year + 1, month, day)


def resolve_dates(raw: RawParse, today: date) -> tuple[date | None, date | None, int | None]:
    """Return (depart_earliest, depart_latest, nights_from_return_date)."""
    if raw.depart_month is None:
        return None, None, None

    month_only = raw.depart_day is None
    if month_only:
        if raw.depart_year is None and raw.depart_month == today.month:
            start = today  # "September" asked on Sept 29 = the rest of this September
        else:
            start = _next_occurrence(raw.depart_month, 1, today, raw.depart_year)
            start = max(start, today)
    else:
        start = _next_occurrence(raw.depart_month, raw.depart_day, today, raw.depart_year)

    # Window end: explicit "between X and Y" > whole month > flex > exact date
    if raw.window_end_month is not None:
        end_day = raw.window_end_day or calendar.monthrange(start.year, raw.window_end_month)[1]
        earliest, latest = start, _on_or_after(raw.window_end_month, end_day, start)
    elif month_only:
        last = calendar.monthrange(start.year, start.month)[1]
        earliest, latest = start, date(start.year, start.month, last)
    elif raw.flex_days:
        flex = timedelta(days=raw.flex_days)
        earliest, latest = max(start - flex, today), start + flex
    else:
        earliest = latest = start

    nights_from_return = None
    if raw.return_day is not None and not month_only:
        # "retour le 9" with no month = same month as departure (or the next one if the day is earlier)
        ret_month = raw.return_month
        if ret_month is None:
            ret_month = start.month if raw.return_day >= start.day else start.month % 12 + 1
        ret = _on_or_after(ret_month, raw.return_day, start)
        nights_from_return = (ret - start).days or None

    return earliest, latest, nights_from_return


def resolve(raw: RawParse, today: date, home_location: str,
            default_max_drive_hours: float = 5.0) -> SearchRequest:
    """Turn the LLM's raw extraction into a validated SearchRequest."""
    warnings: list[str] = []

    earliest, latest, nights_from_return = resolve_dates(raw, today)

    nights_min, nights_max = raw.nights_min, raw.nights_max
    if nights_min is None and nights_max is None and nights_from_return:
        nights_min = nights_max = nights_from_return
    elif nights_min is None and nights_max is not None:
        nights_min = nights_max
    elif nights_max is None and nights_min is not None:
        nights_max = nights_min
    if nights_min and nights_max and nights_min > nights_max:
        nights_min, nights_max = nights_max, nights_min
        warnings.append("nights range was reversed; swapped")

    adults = raw.adults or 2
    if raw.adults is None:
        warnings.append("Number of adults not stated; assumed 2")

    budget_total = None
    if raw.budget_amount is not None:
        travellers = adults + len(raw.children_ages)
        budget_total = raw.budget_amount * travellers if raw.budget_per_person else raw.budget_amount

    origins, airport_warnings = normalize_airports(raw.origin_airports)
    warnings += airport_warnings

    min_stars = raw.min_stars
    if min_stars is not None:
        rounded = round(min_stars * 2) / 2
        if rounded != min_stars:
            warnings.append(f"min_stars {min_stars} rounded to {rounded}")
        min_stars = rounded

    return SearchRequest(
        adults=adults,
        children_ages=sorted(raw.children_ages),
        adults_only_resort=raw.adults_only_resort,
        home_location=home_location,
        destinations=[d.strip() for d in raw.destinations if d.strip()],
        origin_airports=origins or None,
        max_drive_hours=raw.max_drive_hours or default_max_drive_hours,
        depart_earliest=earliest,
        depart_latest=latest,
        nights_min=nights_min,
        nights_max=nights_max,
        trip_type=raw.trip_type,
        min_stars=min_stars,
        direct_flight_only=bool(raw.direct_flight_only),
        max_budget_total_cad=budget_total,
        preferences=[p.strip() for p in raw.preferences if p.strip()],
        language=raw.language,
        warnings=warnings,
    )
