"""Module 3 — app (Flask backend + JSON API), bilingual (en/bg).

A thin web layer over the knowledge base (Module 1) and advice logic (Module 2):

  * ``GET /``            — serves the single-page GUI,
  * ``GET /api/regions`` — the list of supported regions,
  * ``GET /api/advice``  — personalised advice + dated timeline as JSON.

Both API endpoints accept ``?lang=en|bg`` (default ``en``; unknown values fall
back to English). This layer holds no growing logic of its own: it parses query
parameters, delegates to the advisor, and serialises a localized result. Bad or
missing input becomes an HTTP 400 with a friendly, localized ``{"error": ...}``.
"""
from __future__ import annotations

from datetime import date

from flask import Flask, jsonify, render_template, request

from . import advisor, data
from .advisor import PlantingInFutureError
from .data import UnknownRegionError, normalize_lang

# Accept only sensible gardening years. This also keeps all date arithmetic
# (e.g. planting_date + 135 days, or 56 days before transplant) safely inside
# date.min/date.max, so extreme inputs return a clean 400 instead of a 500.
PLANTING_YEAR_MIN = 1900
PLANTING_YEAR_MAX = 2100

# Short month names for frost labels, per language.
_MONTHS = {
    "en": ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "bg": ["", "яну", "фев", "мар", "апр", "май", "юни",
           "юли", "авг", "сеп", "окт", "ное", "дек"],
}

# Localized API error messages (filled with .format(**ctx)).
_ERRORS = {
    "no_region": {"en": "Please choose a region.",
                  "bg": "Моля, изберете регион."},
    "no_date": {"en": "Please provide a planting date (YYYY-MM-DD).",
                "bg": "Моля, въведете дата на сеитба (ГГГГ-ММ-ДД)."},
    "unknown_region": {"en": "Unknown region: {value}.",
                       "bg": "Непознат регион: {value}."},
    "bad_date": {"en": "Invalid planting date: {value}. Use YYYY-MM-DD.",
                 "bg": "Невалидна дата на сеитба: {value}. Използвайте ГГГГ-ММ-ДД."},
    "bad_today": {"en": "Invalid 'today' date: {value}. Use YYYY-MM-DD.",
                  "bg": "Невалидна дата за „днес“: {value}. Използвайте ГГГГ-ММ-ДД."},
    "year_range": {"en": "Planting date year must be between {min} and {max}.",
                   "bg": "Годината на сеитба трябва да е между {min} и {max}."},
}


def create_app() -> Flask:
    """Application factory — build and return a configured Flask app."""
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/regions")
    def api_regions():
        lang = normalize_lang(request.args.get("lang"))
        return jsonify([_region_dict(r, lang) for r in data.list_regions(lang)])

    @app.get("/api/advice")
    def api_advice():
        lang = normalize_lang(request.args.get("lang"))
        region_name = request.args.get("region", "").strip()
        planting_raw = request.args.get("planting_date", "").strip()
        today_raw = request.args.get("today", "").strip()

        if not region_name:
            return _error("no_region", lang)
        if not planting_raw:
            return _error("no_date", lang)

        try:
            region = data.get_region(region_name, lang)
        except UnknownRegionError:
            return _error("unknown_region", lang, value=region_name)

        try:
            planting_date = date.fromisoformat(planting_raw)
        except ValueError:
            return _error("bad_date", lang, value=planting_raw)

        if not PLANTING_YEAR_MIN <= planting_date.year <= PLANTING_YEAR_MAX:
            return _error("year_range", lang, min=PLANTING_YEAR_MIN, max=PLANTING_YEAR_MAX)

        if today_raw:
            try:
                today = date.fromisoformat(today_raw)
            except ValueError:
                return _error("bad_today", lang, value=today_raw)
        else:
            today = date.today()

        return jsonify(_build_advice(region, planting_date, today, lang))

    return app


def _build_advice(region, planting_date: date, today: date, lang: str) -> dict:
    """Assemble the full, localized advice payload."""
    year = planting_date.year
    earliest, latest = advisor.sowing_window(region, year)
    recommended = {
        "sowing_window": {"earliest": earliest.isoformat(), "latest": latest.isoformat()},
        "transplant_date": advisor.transplant_date(region, year).isoformat(),
    }

    try:
        stage = advisor.current_stage(planting_date, today)
    except PlantingInFutureError:
        current = None
        not_started = True
    else:
        localized = data.get_stage(stage.key, lang)
        watering = advisor.watering_advice(stage, region)
        current = {
            "stage_key": stage.key,
            "stage_label": localized.label,
            "stage_description": localized.description,
            "days_since_sowing": (today - planting_date).days,
            "watering": {
                "times_per_week": watering.times_per_week,
                "stage_note": data.watering_rule(stage.key, lang).note,
                "region_note": data.climate_note(watering.climate, lang),
            },
            "tips": data.get_tips(stage.key, lang),
        }
        not_started = False

    timeline = []
    for item in advisor.care_timeline(planting_date):
        loc = data.get_stage(item.stage.key, lang)
        timeline.append({
            "stage_key": item.stage.key,
            "stage_label": loc.label,
            "description": loc.description,
            "start": item.start.isoformat(),
        })

    return {
        "lang": lang,
        "region": _region_dict(region, lang),
        "planting_date": planting_date.isoformat(),
        "today": today.isoformat(),
        "not_started": not_started,
        "recommended": recommended,
        "current": current,
        "timeline": timeline,
    }


def _region_dict(region, lang: str) -> dict:
    """Serialise a (localized) Region into JSON-friendly, display-ready fields."""
    return {
        "key": region.key,
        "name": region.name,
        "note": region.note,
        "last_frost": _format_md(*region.last_frost, lang),
        "first_frost": _format_md(*region.first_frost, lang),
    }


def _format_md(month: int, day: int, lang: str) -> str:
    """Format a (month, day) pair as a short, localized label, e.g. '25 Apr' / '25 апр'."""
    return f"{day} {_MONTHS[lang][month]}"


def _error(key: str, lang: str, **ctx):
    """Build a localized JSON error response (HTTP 400)."""
    message = _ERRORS[key][lang].format(**ctx)
    return jsonify({"error": message}), 400


# Module-level app so `flask --app tomato_coach.app run` works out of the box.
app = create_app()
if __name__ == "__main__":
    app.run(debug=True)

