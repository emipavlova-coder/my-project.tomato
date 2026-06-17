"""Tests for Module 3 (app) — the Flask backend + JSON API.

Uses Flask's test client (no server, no network). Covers the page, the regions
endpoint, a happy-path advice request, the future-planting case, and three
error cases (unknown region, bad date, missing params).
"""
import pytest

from tomato_coach.app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_index_serves_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.content_type


def test_regions_endpoint_returns_known_regions(client):
    resp = client.get("/api/regions")
    assert resp.status_code == 200
    payload = resp.get_json()
    assert isinstance(payload, list) and payload
    names = [r["name"] for r in payload]
    assert "Central Europe" in names
    assert all({"name", "note", "last_frost", "first_frost"} <= set(r) for r in payload)


def test_advice_happy_path(client):
    resp = client.get("/api/advice", query_string={
        "region": "Central Europe",
        "planting_date": "2026-04-01",
        "today": "2026-06-16",
    })
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["not_started"] is False
    assert payload["current"]["days_since_sowing"] == 76
    assert payload["current"]["stage_key"] == "vegetative"   # day 76 → vegetative (56..84)
    assert payload["current"]["tips"]
    assert payload["current"]["watering"]["times_per_week"] >= 1
    assert payload["recommended"]["transplant_date"] == "2026-04-25"
    assert len(payload["timeline"]) == 7


def test_advice_future_planting_marks_not_started(client):
    resp = client.get("/api/advice", query_string={
        "region": "Central Europe",
        "planting_date": "2026-05-01",
        "today": "2026-04-01",
    })
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["not_started"] is True
    assert payload["current"] is None
    assert len(payload["timeline"]) == 7   # the forward plan is still provided


def test_advice_unknown_region_returns_400(client):
    resp = client.get("/api/advice", query_string={
        "region": "Atlantis", "planting_date": "2026-04-01"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_advice_bad_date_returns_400(client):
    resp = client.get("/api/advice", query_string={
        "region": "Central Europe", "planting_date": "not-a-date"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_advice_missing_params_returns_400(client):
    resp = client.get("/api/advice")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_advice_extreme_date_returns_400_not_500(client):
    # Regression: a date near date.max used to overflow timedelta math -> HTTP 500.
    # It must now be rejected cleanly as a 400, never crash.
    resp = client.get("/api/advice", query_string={
        "region": "Central Europe", "planting_date": "9999-12-31"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


# --- bilingual (Module 5) ---------------------------------------------------

def _has_cyrillic(text):
    return any("Ѐ" <= ch <= "ӿ" for ch in text)


def test_advice_in_bulgarian(client):
    resp = client.get("/api/advice", query_string={
        "region": "central-europe",
        "planting_date": "2026-04-15",
        "today": "2026-06-16",
        "lang": "bg",
    })
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["lang"] == "bg"
    assert payload["region"]["name"] == "Централна Европа"
    assert payload["current"]["stage_label"] == "Вегетативен растеж"
    assert _has_cyrillic(payload["current"]["watering"]["region_note"])
    assert _has_cyrillic(" ".join(payload["current"]["tips"]))


def test_regions_endpoint_bulgarian(client):
    payload = client.get("/api/regions?lang=bg").get_json()
    names = [r["name"] for r in payload]
    assert "Централна Европа" in names
    assert all("key" in r for r in payload)
    assert all(_has_cyrillic(r["name"]) for r in payload)


def test_advice_accepts_region_key_and_defaults_to_english(client):
    payload = client.get("/api/advice", query_string={
        "region": "central-europe", "planting_date": "2026-04-15", "today": "2026-06-16",
    }).get_json()
    assert payload["lang"] == "en"
    assert payload["region"]["name"] == "Central Europe"


def test_error_message_localized_in_bulgarian(client):
    resp = client.get("/api/advice", query_string={"lang": "bg"})
    assert resp.status_code == 400
    assert _has_cyrillic(resp.get_json()["error"])
