"""Module 2 — advisor (core logic).

Pure, deterministic functions that turn the knowledge base (Module 1) plus a
user's region and dates into concrete advice:

  * ``sowing_window`` / ``transplant_date`` — recommended calendar dates for a region,
  * ``current_stage``  — which growth stage a planting is in on a given day,
  * ``watering_advice`` — stage watering rule, nudged by the region's climate,
  * ``care_timeline``  — the full dated plan from sowing to harvest.

Every function takes its dates as arguments (no hidden "today"), so results are
deterministic and easy to test. ``planting_date`` always means the *sowing* day.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from . import data
from .data import Region, Stage

# Fixed non-leap reference year for region season-length math (year-independent).
_REF_YEAR = 2001
# A frost-free season at least this long counts as "long & warm" (waters more).
_LONG_WARM_SEASON_DAYS = 230


class PlantingInFutureError(ValueError):
    """Raised when the current stage is requested but planting date is after 'today'."""


@dataclass(frozen=True)
class StageDate:
    """A growth stage paired with the calendar date it begins for a given planting."""

    stage: Stage
    start: date


@dataclass(frozen=True)
class WateringAdvice:
    """Watering guidance for a stage, adjusted for the region's climate.

    ``climate`` is a language-free key ('warm' or 'cool'); the web layer turns
    it into a localized note via ``data.climate_note``.
    """

    times_per_week: int
    climate: str


def transplant_date(region: Region, year: int) -> date:
    """Recommended date to move plants outdoors: the region's average last frost."""
    month, day = region.last_frost
    return date(year, month, day)


def sowing_window(region: Region, year: int) -> tuple[date, date]:
    """Recommended window to sow indoors: about 6–8 weeks before transplanting."""
    transplant = transplant_date(region, year)
    six_weeks = data.get_stage("transplant").start_day  # 42 days from sowing
    latest = transplant - timedelta(days=six_weeks)
    earliest = transplant - timedelta(days=six_weeks + 14)
    return earliest, latest


def current_stage(planting_date: date, today: date) -> Stage:
    """The growth stage a planting is in on ``today`` (planting_date = sowing day)."""
    days = (today - planting_date).days
    if days < 0:
        raise PlantingInFutureError(
            f"Planting date {planting_date.isoformat()} is after today {today.isoformat()}."
        )
    current = data.STAGES[0]
    for stage in data.STAGES:
        if stage.start_day <= days:
            current = stage
        else:
            break
    return current


def watering_advice(stage: Stage, region: Region) -> WateringAdvice:
    """Watering frequency + climate key for a stage, by the region's season length."""
    base = data.watering_rule(stage.key).times_per_week
    if _season_length_days(region) >= _LONG_WARM_SEASON_DAYS:
        return WateringAdvice(times_per_week=base + 1, climate="warm")
    return WateringAdvice(times_per_week=base, climate="cool")


def care_timeline(planting_date: date) -> list[StageDate]:
    """Calendar of every growth stage for a planting sown on ``planting_date``."""
    return [
        StageDate(stage, planting_date + timedelta(days=stage.start_day))
        for stage in data.STAGES
    ]


def _season_length_days(region: Region) -> int:
    """Frost-free days between the average last and first frost (year-independent)."""
    start = date(_REF_YEAR, *region.last_frost)
    end = date(_REF_YEAR, *region.first_frost)
    return (end - start).days
