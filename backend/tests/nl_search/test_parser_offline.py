"""Offline tests: no Ollama needed. Run with:  pytest -q"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
import yaml

from app.nl_search.evaluate import compare
from app.nl_search.models import RawParse, SearchRequest
from app.nl_search.parser import ParseError, parse_request
from app.nl_search.resolve import normalize_airports, resolve, resolve_dates

SUITE = yaml.safe_load((Path(__file__).parent / "cases.yaml").read_text(encoding="utf-8"))
TODAY = date.fromisoformat(SUITE["today"])
HOME = SUITE["home_location"]

# What a perfect LLM should extract for each case (language extraction only, no math).
IDEAL_RAW = {
    "en01": dict(adults=2, adults_only_resort=True, trip_type="all_inclusive", min_stars=4.5,
                 direct_flight_only=True, depart_month=2, nights_min=7, nights_max=7,
                 budget_amount=3000, budget_per_person=False),
    "en02": dict(trip_type="flight_only", origin_airports=["BTV", "BOS"], destinations=["Dallas"],
                 depart_month=3, depart_day=12, depart_year=2027, return_month=3, return_day=19),
    "en03": dict(adults=2, children_ages=[9, 6], trip_type="all_inclusive", destinations=["Punta Cana"],
                 depart_month=3, depart_day=1, window_end_month=3, window_end_day=14,
                 nights_min=6, nights_max=8, budget_amount=6000, budget_per_person=False),
    "en04": dict(trip_type="hotel_only", destinations=["Cancun"], min_stars=5,
                 depart_month=1, depart_day=15, nights_min=4, nights_max=4),
    "en05": dict(adults=2, trip_type="all_inclusive", destinations=["Mexico"], min_stars=4,
                 depart_month=1, nights_min=10, nights_max=14, preferences=["quiet", "nice beach"]),
    "en06": dict(adults=3, trip_type="flight_hotel", destinations=["Orlando"], direct_flight_only=True,
                 depart_month=12, depart_day=20, flex_days=3, nights_min=7, nights_max=7),
    "en07": dict(adults=2, adults_only_resort=True, trip_type="all_inclusive", destinations=["Caribbean"],
                 depart_month=11, nights_min=7, nights_max=7, budget_amount=1500, budget_per_person=True),
    "en08": dict(trip_type="all_inclusive", origin_airports=["Toronto"], destinations=["Cuba"],
                 min_stars=4.5, depart_month=4, nights_min=14, nights_max=14, max_drive_hours=6),
    "en09": dict(preferences=["warm"]),
    "en10": dict(adults=2, children_ages=[12], trip_type="flight_only", origin_airports=["YUL"],
                 destinations=["Paris"], direct_flight_only=True, depart_month=5, depart_day=3,
                 depart_year=2027, nights_min=10, nights_max=10),
    "fr01": dict(adults=2, adults_only_resort=True, trip_type="all_inclusive", min_stars=4.5,
                 direct_flight_only=True, depart_month=2, nights_min=7, nights_max=7,
                 budget_amount=3000, budget_per_person=False, language="fr"),
    "fr02": dict(trip_type="flight_only", origin_airports=["PBG"], destinations=["Fort Lauderdale"],
                 depart_month=1, depart_day=8, depart_year=2027, return_month=1, return_day=15, language="fr"),
    "fr03": dict(adults=2, children_ages=[5, 8], trip_type="all_inclusive", destinations=["Varadero"],
                 depart_month=3, depart_day=1, window_end_month=3, window_end_day=10,
                 nights_min=6, nights_max=8, language="fr"),
    "fr04": dict(trip_type="hotel_only", destinations=["Montego Bay"], min_stars=5,
                 depart_month=12, depart_day=20, nights_min=5, nights_max=5, language="fr"),
    "fr05": dict(adults=2, trip_type="all_inclusive", destinations=["Mexique"], min_stars=4,
                 depart_month=1, nights_min=10, nights_max=14,
                 preferences=["resort tranquille", "belle plage"], language="fr"),
    "fr06": dict(adults=3, trip_type="flight_hotel", destinations=["New York"],
                 depart_month=10, depart_day=10, flex_days=2, nights_min=4, nights_max=4, language="fr"),
    "fr07": dict(adults=2, adults_only_resort=True, trip_type="all_inclusive", destinations=["Caraïbes"],
                 depart_month=11, nights_min=7, nights_max=7, budget_amount=1500,
                 budget_per_person=True, language="fr"),
    "fr08": dict(trip_type="flight_only", origin_airports=["Boston"], destinations=["Dallas"],
                 direct_flight_only=True, depart_month=2, depart_day=5, depart_year=2027,
                 return_month=2, return_day=9, language="fr"),
    "fr09": dict(preferences=["au chaud"], language="fr"),
    "fr10": dict(trip_type="all_inclusive", origin_airports=["BTV", "Montréal"], destinations=["Punta Cana"],
                 depart_month=4, nights_min=14, nights_max=14, max_drive_hours=3, language="fr"),
}


def test_suite_has_10_en_and_10_fr():
    ids = [c["id"] for c in SUITE["cases"]]
    assert len(ids) == 20 == len(set(ids))
    assert sum(i.startswith("en") for i in ids) == 10
    assert set(ids) == set(IDEAL_RAW)


@pytest.mark.parametrize("case", SUITE["cases"], ids=lambda c: c["id"])
def test_ideal_extraction_passes(case):
    """If the LLM extracts perfectly, the Python resolver must produce the expected request."""
    request = resolve(RawParse(**IDEAL_RAW[case["id"]]), today=TODAY, home_location=HOME)
    assert compare(request, case["expect"]) == []


def test_compare_catches_wrong_answer():
    case = next(c for c in SUITE["cases"] if c["id"] == "en01")
    wrong = dict(IDEAL_RAW["en01"], min_stars=4.0, budget_per_person=True)
    errors = compare(resolve(RawParse(**wrong), TODAY, HOME), case["expect"])
    assert any("min_stars" in e for e in errors)
    assert any("max_budget_total_cad" in e for e in errors)


# --- resolver details -------------------------------------------------------

def test_month_already_passed_rolls_to_next_year():
    earliest, latest, _ = resolve_dates(RawParse(depart_month=8), today=TODAY)
    assert (earliest, latest) == (date(2027, 8, 1), date(2027, 8, 31))


def test_current_month_starts_today():
    earliest, latest, _ = resolve_dates(RawParse(depart_month=9), today=TODAY)
    assert (earliest, latest) == (TODAY, date(2026, 9, 30))


def test_flex_never_starts_in_the_past():
    earliest, latest, _ = resolve_dates(RawParse(depart_month=10, depart_day=1, flex_days=5), today=TODAY)
    assert earliest == TODAY and latest == date(2026, 10, 6)


def test_invalid_day_is_clamped():
    earliest, _, _ = resolve_dates(RawParse(depart_month=2, depart_day=30), today=TODAY)
    assert earliest == date(2027, 2, 28)


def test_return_date_crossing_new_year():
    _, _, nights = resolve_dates(RawParse(depart_month=12, depart_day=27, return_month=1, return_day=3), TODAY)
    assert nights == 7


def test_budget_per_person_includes_children():
    raw = RawParse(adults=2, children_ages=[6, 9], budget_amount=1200, budget_per_person=True)
    assert resolve(raw, TODAY, HOME).max_budget_total_cad == 4800


def test_airport_names_and_accents():
    codes, warnings = normalize_airports(["Montréal", "boston", "PBG", "YUL", "Timbuktu"])
    assert codes == ["YUL", "BOS", "PBG"]
    assert len(warnings) == 1


def test_missing_adults_defaults_with_warning():
    request = resolve(RawParse(), TODAY, HOME)
    assert request.adults == 2 and any("adults" in w for w in request.warnings)


def test_flight_only_one_way_does_not_need_nights():
    raw = RawParse(trip_type="flight_only", depart_month=3, depart_day=12)
    assert resolve(raw, TODAY, HOME).missing_fields() == []


def test_search_request_rejects_reversed_dates():
    with pytest.raises(ValueError):
        SearchRequest(home_location=HOME, depart_earliest=date(2027, 3, 1), depart_latest=date(2027, 2, 1))


# --- parser retry logic with a fake LLM --------------------------------------

class FakeClient:
    def __init__(self, replies):
        self.replies, self.calls = list(replies), []

    def chat(self, messages, schema):
        self.calls.append(messages)
        return self.replies.pop(0)


def test_parser_retries_once_on_bad_json():
    good = json.dumps(IDEAL_RAW["en04"])
    client = FakeClient(["not json", good])
    result = parse_request("Hotel only in Cancun...", client=client, today=TODAY, home_location=HOME)
    assert result.attempts == 2 and result.request.trip_type == "hotel_only"
    assert "rejected" in client.calls[1][-1]["content"]


def test_parser_gives_up_after_two_failures():
    client = FakeClient(['{"min_stars": 9}', '{"min_stars": 9}'])
    with pytest.raises(ParseError):
        parse_request("x", client=client, today=TODAY, home_location=HOME)


def test_schema_sent_to_ollama_is_valid_json_schema():
    schema = RawParse.model_json_schema()
    assert schema["type"] == "object" and "depart_month" in schema["properties"]


# --- regressions from the first qwen2.5:32b run (15/20) --------------------------

@pytest.mark.parametrize("written, code", [
    ("Plattsburgh", "PBG"), ("Plattsburgh, NY", "PBG"), ("Boston Logan", "BOS"),
    ("Montréal-Trudeau", "YUL"), ("Montréal Saint-Hubert", "YHU"), ("Quebec City", "YQB"),
    ("Burlington, VT", "BTV"), ("Toronto Pearson", "YYZ"), ("btv", "BTV"),
])
def test_written_airport_names_map_to_codes(written, code):
    assert normalize_airports([written])[0] == [code]


def test_return_day_without_month_uses_departure_month():
    # "aller le 5 février 2027 et retour le 9"
    _, _, nights = resolve_dates(RawParse(depart_month=2, depart_day=5, depart_year=2027, return_day=9), TODAY)
    assert nights == 4


def test_return_day_earlier_than_departure_rolls_to_next_month():
    # "leaving January 28, back on the 3rd"
    _, _, nights = resolve_dates(RawParse(depart_month=1, depart_day=28, return_day=3), TODAY)
    assert nights == 6


def test_prompt_examples_are_valid_and_do_not_leak_test_cases():
    from app.nl_search.prompts import SYSTEM_PROMPT
    examples = [line for line in SYSTEM_PROMPT.split("EXAMPLES", 1)[1].split("\n\n")
                if line.strip().startswith("Request:")]
    assert len(examples) == 3
    for block in examples:
        request_line, json_text = block.strip().split("\n", 1)
        RawParse.model_validate(json.loads(json_text))         # valid against the schema
        for case in SUITE["cases"]:
            for place in case["expect"].get("destinations", []):
                assert place.lower() not in block.lower(), f"example reuses test destination {place}"
