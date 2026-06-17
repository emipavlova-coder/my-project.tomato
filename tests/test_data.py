"""Tests for Module 1 (data) — the offline knowledge base.

Covers happy-path lookups, an error case, and data-integrity checks that
guard against the dataset drifting out of sync (e.g. a stage with no tips).
"""
import pytest

from tomato_coach import data
from tomato_coach.data import (
    Region,
    WateringRule,
    UnknownRegionError,
    UnknownStageError,
)


def test_list_regions_nonempty_and_unique():
    regions = data.list_regions()
    assert len(regions) >= 3
    assert all(isinstance(r, Region) and r.name for r in regions)
    names = [r.name for r in regions]
    assert len(names) == len(set(names))  # no duplicate region names


def test_get_region_is_case_insensitive():
    region = data.get_region("central europe")
    assert region.name == "Central Europe"
    # Spring frost should fall before the autumn frost (sane frost-free window).
    assert region.last_frost < region.first_frost


def test_get_region_unknown_raises():
    with pytest.raises(UnknownRegionError):
        data.get_region("Atlantis")


def test_get_region_empty_raises():
    with pytest.raises(UnknownRegionError):
        data.get_region("")


def test_stages_are_ordered_and_unique_by_start_day():
    days = [s.start_day for s in data.STAGES]
    assert days == sorted(days)          # chronological order
    assert len(set(days)) == len(days)   # strictly increasing, no overlaps


def test_every_stage_has_tips_and_a_watering_rule():
    for stage in data.STAGES:
        tips = data.get_tips(stage.key)
        assert tips, f"no tips for stage {stage.key!r}"
        rule = data.watering_rule(stage.key)
        assert isinstance(rule, WateringRule)
        assert rule.times_per_week >= 1
        assert rule.note


def test_hilling_advice_is_present():
    # The user specifically asked for hilling / earthing-up guidance.
    all_tips = " ".join(
        tip for stage in data.STAGES for tip in data.get_tips(stage.key)
    ).lower()
    assert "hill" in all_tips or "earth" in all_tips


def test_get_stage_known_and_unknown():
    assert data.get_stage("flowering").label == "Flowering"
    with pytest.raises(UnknownStageError):
        data.get_stage("not-a-stage")


def test_get_tips_unknown_raises():
    with pytest.raises(UnknownStageError):
        data.get_tips("not-a-stage")


def test_watering_rule_unknown_raises():
    with pytest.raises(UnknownStageError):
        data.watering_rule("not-a-stage")


# --- bilingual (Module 5) ---------------------------------------------------

def _has_cyrillic(text):
    return any("Ѐ" <= ch <= "ӿ" for ch in text)


def test_all_region_text_localized_in_both_languages():
    en = data.list_regions("en")
    bg = data.list_regions("bg")
    assert [r.key for r in en] == [r.key for r in bg]  # same regions, same order
    for r_en, r_bg in zip(en, bg):
        assert r_en.name and r_bg.name and r_en.name != r_bg.name
        assert r_en.note and r_bg.note and r_en.note != r_bg.note
        assert _has_cyrillic(r_bg.name) and _has_cyrillic(r_bg.note)


def test_all_stage_and_tip_text_localized():
    for stage in data.STAGES:
        s_en = data.get_stage(stage.key, "en")
        s_bg = data.get_stage(stage.key, "bg")
        assert s_en.label != s_bg.label
        assert _has_cyrillic(s_bg.label) and _has_cyrillic(s_bg.description)
        en_tips = data.get_tips(stage.key, "en")
        bg_tips = data.get_tips(stage.key, "bg")
        assert len(en_tips) == len(bg_tips)
        assert all(bg_tips) and _has_cyrillic(" ".join(bg_tips))


def test_get_region_by_key_and_localized_name():
    assert data.get_region("central-europe", "bg").name == "Централна Европа"
    assert data.get_region("Централна Европа").key == "central-europe"
    assert data.get_region("Central Europe", "en").name == "Central Europe"


def test_bulgarian_hilling_advice_present():
    bg_tips = " ".join(
        tip for stage in data.STAGES for tip in data.get_tips(stage.key, "bg")
    )
    assert "загърл" in bg_tips  # earthing-up / hilling, in Bulgarian


def test_unknown_language_falls_back_to_english():
    assert data.normalize_lang("fr") == "en"
    assert data.normalize_lang(None) == "en"
    assert data.normalize_lang("bg") == "bg"
    assert data.get_region("central-europe", "fr").name == "Central Europe"


def test_climate_note_localized():
    assert _has_cyrillic(data.climate_note("warm", "bg"))
    assert data.climate_note("warm", "en") != data.climate_note("warm", "bg")
