"""Tests untuk src.form_state — operasi form tanpa Streamlit."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.form_state import (
    PENDING_PRESET_KEY,
    apply_pending_preset,
    apply_widget_values,
    build_raw_input,
    missing_raw_fields,
    request_preset,
    seed_widget_state,
)
from src.field_spec import FORM_DEFAULTS, MODULE_FIELDS, widget_key


def test_seed_only_fills_missing_widgets():
    state = {widget_key("gender"): "F"}

    seed_widget_state(state)

    assert state[widget_key("gender")] == "F"
    assert state[widget_key("region")] == FORM_DEFAULTS["region"]
    assert set(state) == {widget_key(field) for field in FORM_DEFAULTS}


def test_apply_widget_values_uses_widget_keys():
    state = {}

    apply_widget_values(state, {"gender": "F", "studied_credits": 120})

    assert state == {widget_key("gender"): "F", widget_key("studied_credits"): 120}


def test_pending_preset_is_applied_once():
    state = {}
    request_preset(state, {"gender": "F"})

    assert state[PENDING_PRESET_KEY] == {"gender": "F"}
    assert apply_pending_preset(state) == {"gender": "F"}
    assert state[widget_key("gender")] == "F"
    assert PENDING_PRESET_KEY not in state
    assert apply_pending_preset(state) is None


def test_build_raw_input_includes_module_fields():
    form_values = {field: f"nilai-{field}" for field in FORM_DEFAULTS}

    raw = build_raw_input(form_values, "CCC", "2014B")

    assert raw["code_module"] == "CCC"
    assert raw["code_presentation"] == "2014B"
    assert raw["gender"] == "nilai-gender"
    for field in MODULE_FIELDS:
        # Nilai modul diambil dari widget di luar form, bukan dari form_values.
        assert raw[field] != form_values[field]


def test_build_raw_input_reports_missing_values_as_none():
    raw = build_raw_input({"gender": "M"}, "AAA", "2013J")

    assert raw["gender"] == "M"
    assert raw["region"] is None


def test_missing_raw_fields_detects_absent_keys():
    raw = build_raw_input({field: 0 for field in FORM_DEFAULTS}, "AAA", "2013J")
    del raw["region"]

    assert missing_raw_fields(raw) == ["region"]
    assert missing_raw_fields(raw, ["gender", "region"]) == ["region"]
