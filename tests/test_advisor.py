"""Tests for Module 2 (advisor) — the deterministic advice logic.

Covers recommended dates, stage progression (incl. a boundary day), the
future-date error, a leap-year span, and the region-based watering rule.
"""
import datetime as dt
from datetime import date

import pytest

from tomato_coach import advisor, data
from tomato_coach.advisor import StageDate, WateringAdvice, PlantingInFutureError


def test_transplant_date_is_region_last_frost():
    region = data.get_region("Central Europe")  # last frost 25 Apr
    assert advisor.transplant_date(region, 2026) == date(2026, 4, 25)


def test_sowing_window_is_six_to_eight_weeks_before_transplant():
    region = data.get_region("Central Europe")
    earliest, latest = advisor.sowing_window(region, 2026)
    transplant = advisor.transplant_date(region, 2026)
    assert latest == transplant - dt.timedelta(days=42)    # 6 weeks before
    assert earliest == transplant - dt.timedelta(days=56)  # 8 weeks before
    assert earliest < latest < transplant


def test_current_stage_progression_and_boundary():
    plant = date(2026, 4, 1)
    assert advisor.current_stage(plant, plant).key == "germination"                      # day 0
    assert advisor.current_stage(plant, plant + dt.timedelta(days=41)).key == "seedling"  # day 41
    assert advisor.current_stage(plant, plant + dt.timedelta(days=42)).key == "transplant"  # boundary
    assert advisor.current_stage(plant, plant + dt.timedelta(days=200)).key == "harvest"  # well past


def test_current_stage_before_planting_raises():
    plant = date(2026, 4, 1)
    with pytest.raises(PlantingInFutureError):
        advisor.current_stage(plant, plant - dt.timedelta(days=1))


def test_care_timeline_dates_match_offsets_and_increase():
    plant = date(2026, 4, 1)
    timeline = advisor.care_timeline(plant)
    assert len(timeline) == len(data.STAGES)
    assert all(isinstance(item, StageDate) for item in timeline)
    assert timeline[0].start == plant  # first stage starts on the sowing day
    for item in timeline:
        assert item.start == plant + dt.timedelta(days=item.stage.start_day)
    starts = [item.start for item in timeline]
    assert starts == sorted(starts)
    assert len(set(starts)) == len(starts)  # strictly increasing


def test_care_timeline_handles_leap_year_span():
    plant = date(2024, 1, 15)  # 2024 is a leap year
    harvest = advisor.care_timeline(plant)[-1]
    assert harvest.stage.key == "harvest"
    assert (harvest.start - plant).days == 135  # exact 135-day span across 29 Feb


def test_watering_advice_warm_region_waters_more():
    veg = data.get_stage("vegetative")
    warm = data.get_region("Mediterranean")    # long, warm season
    cool = data.get_region("Central Europe")   # moderate season
    base = data.watering_rule("vegetative").times_per_week

    warm_advice = advisor.watering_advice(veg, warm)
    cool_advice = advisor.watering_advice(veg, cool)

    assert isinstance(warm_advice, WateringAdvice)
    assert warm_advice.times_per_week == base + 1
    assert cool_advice.times_per_week == base
    assert warm_advice.climate == "warm"
    assert cool_advice.climate == "cool"
