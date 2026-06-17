"""Tests for Module 4 (frontend) — verifies the served page is wired to the API.

The JavaScript itself is a thin renderer and is verified by running the app and
capturing screenshots (a graded deliverable). Here we check, deterministically,
that Flask serves the page with the DOM hooks the JS depends on and that the
static JS/CSS assets are reachable.
"""
import pytest

from tomato_coach.app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_page_has_form_and_mount_points(client):
    html = client.get("/").get_data(as_text=True)
    # form controls the JS reads
    assert 'id="advice-form"' in html
    assert 'id="region"' in html
    assert 'id="planting-date"' in html
    # result mount points the JS fills in
    for hook in ('id="results"', 'id="recommended"', 'id="current"', 'id="timeline"', 'id="error"'):
        assert hook in html
    # assets are linked
    assert "app.js" in html
    assert "style.css" in html


def test_static_assets_are_served(client):
    js = client.get("/static/app.js")
    assert js.status_code == 200
    assert "fetch(" in js.get_data(as_text=True)  # it really calls the API

    css = client.get("/static/style.css")
    assert css.status_code == 200
    assert ".card" in css.get_data(as_text=True)


def test_page_has_language_switch(client):
    html = client.get("/").get_data(as_text=True)
    assert 'id="lang-switch"' in html
    assert 'data-lang="en"' in html
    assert 'data-lang="bg"' in html


def test_app_js_has_bilingual_chrome(client):
    js = client.get("/static/app.js").get_data(as_text=True)
    assert "I18N" in js
    assert "bg:" in js  # Bulgarian chrome strings present in the dictionary
