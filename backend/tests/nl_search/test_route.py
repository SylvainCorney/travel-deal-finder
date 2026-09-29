"""Endpoint tests with a fake LLM — no Ollama or database needed."""
from __future__ import annotations

import json
from datetime import date

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import nl_search
from tests.nl_search.test_parser_offline import IDEAL_RAW

TODAY = date(2026, 9, 29)


class FakeClient:
    def __init__(self, reply=None, error=None):
        self.reply, self.error = reply, error

    def chat(self, messages, schema):
        if self.error:
            raise self.error
        return json.dumps(self.reply)


def make_client(fake: FakeClient) -> TestClient:
    app = FastAPI()
    app.include_router(nl_search.router, prefix="/api/v1/nl-search")
    app.dependency_overrides[nl_search.get_llm_client] = lambda: fake
    app.dependency_overrides[nl_search.get_today] = lambda: TODAY
    return TestClient(app)


def post(fake, text="test request"):
    return make_client(fake).post("/api/v1/nl-search/parse", json={"text": text})


def test_complete_request_returns_legacy_search():
    resp = post(FakeClient(IDEAL_RAW["en04"]))           # hotel only, Cancun, Jan 15, 4 nights
    assert resp.status_code == 200
    body = resp.json()
    assert body["missing"] == [] and body["question"] is None
    assert body["legacy_search"] == {
        "origin": "YUL", "location": "Cancun",
        "check_in_date": "2027-01-15", "check_out_date": "2027-01-19",
        "hotels": [], "airlines": [], "sources": ["hotels"],
    }
    assert body["legacy_note"] is None


def test_multi_airport_and_window_are_reported_in_note():
    body = post(FakeClient(IDEAL_RAW["en02"])).json()     # BTV or BOS -> Dallas
    assert body["legacy_search"]["origin"] == "BTV"
    assert body["legacy_search"]["sources"] == ["flights"]
    assert "BOS" in body["legacy_note"]


def test_month_window_uses_first_date_and_mentions_flexibility():
    body = post(FakeClient(IDEAL_RAW["en05"])).json()     # Mexico, January, 10-14 nights
    assert body["legacy_search"]["check_in_date"] == "2027-01-01"
    assert body["legacy_search"]["check_out_date"] == "2027-01-11"
    assert "2027-01-31" in body["legacy_note"] and "14 nights" in body["legacy_note"]


def test_vague_request_asks_one_question_in_french():
    body = post(FakeClient(IDEAL_RAW["fr09"])).json()     # "Je veux partir au chaud"
    assert set(body["missing"]) == {"dates", "nights", "trip_type"}
    assert body["question"].startswith("Quand")
    assert body["legacy_search"] is None


def test_missing_only_trip_type_asks_about_trip_type():
    raw = dict(IDEAL_RAW["en04"]); raw.pop("trip_type")
    body = post(FakeClient(raw)).json()
    assert body["missing"] == ["trip_type"]
    assert "all-inclusive" in body["question"]


def test_no_destination_explains_why_search_cannot_run():
    body = post(FakeClient(IDEAL_RAW["en01"])).json()     # complete, but no destination
    assert body["missing"] == [] and body["legacy_search"] is None
    assert "destination" in body["legacy_note"]


def test_ollama_down_returns_503():
    resp = post(FakeClient(error=httpx.ConnectError("refused")))
    assert resp.status_code == 503 and "Ollama" in resp.json()["detail"]


def test_model_nonsense_returns_422():
    resp = post(FakeClient({"min_stars": 9}))
    assert resp.status_code == 422


def test_text_too_short_is_rejected():
    assert post(FakeClient(IDEAL_RAW["en04"]), text="hi").status_code == 422
