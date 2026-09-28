"""Tests untuk src/form_config.py dan src/assets.py."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.assets import ASSETS_DIR, FIGURES, asset_path, available, missing
from src.config import (
    CATEGORICAL_COLS, FEATURE_ORDER, REQUIRED_INPUT_FIELDS,
)
from src.form_config import (
    AMBANG_EFFECT, CONTOH_BERISIKO, CONTOH_TIDAK_BERISIKO, DIRECTION_LABEL,
    FIELD_BOUNDS, FIELD_EFFECT, FIELD_HELP, FIELD_LABELS, FORM_DEFAULTS,
    FORM_KOSONG, FORM_SECTIONS, MODULE_FIELDS, NON_MODEL_FORM_FIELDS,
    NUMERIC_FORM_FIELDS, PRESETS, SELECT_OPTIONS, effect_rows, field_effect,
    field_help, field_label, validate_form_config, widget_key,
)

# Field yang boleh tidak ada di FORM_DEFAULTS karena dipakai sebagai selectbox
# dengan opsi dari config, bukan dari default dict.
CATEGORICAL_FIELDS = set(CATEGORICAL_COLS) | {"code_module", "code_presentation"}


class TestFormConfigConsistency:
    def test_validate_form_config_reports_no_problems(self):
        assert validate_form_config() == []

    def test_every_form_field_has_a_label(self):
        for field in FORM_DEFAULTS:
            assert field in FIELD_LABELS, f"label hilang untuk {field}"
            assert FIELD_LABELS[field].strip()

    def test_every_select_option_field_has_options(self):
        for field in SELECT_OPTIONS:
            assert len(SELECT_OPTIONS[field]) >= 2
            assert field in FIELD_LABELS

    def test_every_numeric_field_has_bounds(self):
        for field in NUMERIC_FORM_FIELDS:
            low, high, step = FIELD_BOUNDS[field]
            assert low < high, f"bounds tidak valid untuk {field}"
            assert step > 0, f"step tidak valid untuk {field}"

    def test_defaults_sit_inside_bounds(self):
        for field in NUMERIC_FORM_FIELDS:
            low, high, _ = FIELD_BOUNDS[field]
            assert low <= FORM_DEFAULTS[field] <= high, f"default di luar batas {field}"

    def test_every_field_has_help_text(self):
        for field in FORM_DEFAULTS:
            assert field in FIELD_HELP, f"help hilang untuk {field}"

    def test_help_text_is_a_sentence(self):
        """Help minimal satu kalimat dan diakhiri titik."""
        for field, text in FIELD_HELP.items():
            assert text.strip().endswith("."), f"help {field} tidak diakhiri titik"
            assert len(text) > 10, f"help {field} terlalu pendek"

    def test_sections_cover_every_form_field_exactly_once(self):
        listed = [field for _, fields in FORM_SECTIONS for field in fields]

        assert len(listed) == len(set(listed)), "ada field yang dobel"
        assert set(listed) == set(FORM_DEFAULTS) - set(MODULE_FIELDS), (
            "FORM_SECTIONS harus mencakup semua field kecuali MODULE_FIELDS"
        )

    def test_module_fields_are_exactly_module_and_presentation(self):
        assert MODULE_FIELDS == ["code_module", "code_presentation"]

    def test_module_fields_are_rendered_outside_the_form(self):
        for field in MODULE_FIELDS:
            assert all(field not in fields for _, fields in FORM_SECTIONS)

    def test_sections_are_numbered_and_titled(self):
        for position, (title, fields) in enumerate(FORM_SECTIONS, 1):
            assert title.startswith(f"{position}.")
            assert fields

    def test_numeric_and_select_fields_partition_the_form(self):
        assert set(NUMERIC_FORM_FIELDS) | set(SELECT_OPTIONS) == set(FORM_DEFAULTS)
        assert not set(NUMERIC_FORM_FIELDS) & set(SELECT_OPTIONS)

    def test_categorical_fields_are_selectboxes(self):
        for field in CATEGORICAL_FIELDS & set(FORM_DEFAULTS):
            assert field in SELECT_OPTIONS, f"{field} seharusnya selectbox"


class TestWidgetKeys:
    def test_keys_are_namespaced_per_field(self):
        keys = {widget_key(field) for field in FORM_DEFAULTS}

        assert len(keys) == len(FORM_DEFAULTS)
        assert all(key.startswith("f_") for key in keys)

    def test_same_field_always_maps_to_same_key(self):
        assert widget_key("gender") == widget_key("gender")
        assert widget_key("gender") != widget_key("region")


class TestFieldLabel:
    def test_uses_configured_label(self):
        assert field_label("gender") == FIELD_LABELS["gender"]

    def test_falls_back_to_field_name(self):
        assert field_label("field_tidak_dikenal") == "field_tidak_dikenal"


class TestPresets:
    def test_form_kosong_mengosongkan_setiap_field(self):
        assert set(FORM_KOSONG) == set(FORM_DEFAULTS)
        assert all(value is None for value in FORM_KOSONG.values())

    def test_form_kosong_bukan_anggota_presets(self):
        """PRESETS berisi data lengkap yang harus lolos validasi, form kosong tidak."""
        assert FORM_KOSONG not in PRESETS.values()
        assert set(PRESETS) == {"Contoh berisiko", "Contoh tidak berisiko"}

    @pytest.mark.parametrize(
        "preset", [CONTOH_BERISIKO, CONTOH_TIDAK_BERISIKO]
    )
    def test_presets_cover_every_form_field(self, preset):
        assert set(preset) == set(FORM_DEFAULTS)

    @pytest.mark.parametrize(
        "preset", [CONTOH_BERISIKO, CONTOH_TIDAK_BERISIKO]
    )
    def test_presets_respect_widget_bounds(self, preset):
        for field in NUMERIC_FORM_FIELDS:
            low, high, _ = FIELD_BOUNDS[field]
            assert low <= preset[field] <= high, f"{field} di luar batas"

    @pytest.mark.parametrize(
        "preset", [CONTOH_BERISIKO, CONTOH_TIDAK_BERISIKO]
    )
    def test_presets_use_valid_categories(self, preset):
        for field, options in SELECT_OPTIONS.items():
            assert preset[field] in options, f"{field} bukan opsi yang valid"

    def test_presets_differ_from_each_other(self):
        differing = {
            field
            for field in FORM_DEFAULTS
            if CONTOH_BERISIKO[field] != CONTOH_TIDAK_BERISIKO[field]
        }
        assert len(differing) > 10


class TestFieldModelContract:
    def test_form_fields_cover_required_input_fields(self):
        expected = set(REQUIRED_INPUT_FIELDS) | set(NON_MODEL_FORM_FIELDS)

        assert set(FORM_DEFAULTS) == expected

    def test_non_model_fields_are_not_features(self):
        for field in NON_MODEL_FORM_FIELDS:
            assert field not in FEATURE_ORDER, (
                f"{field} ditandai non-model tapi ada di FEATURE_ORDER"
            )

    def test_required_input_fields_are_real_features(self):
        for field in REQUIRED_INPUT_FIELDS:
            if field in ("code_module", "code_presentation"):
                continue
            assert field in FEATURE_ORDER


class TestFieldEffect:
    """Arah nilai harus menutup semua field numerik dan konsisten dengan ambang."""

    def test_every_numeric_field_has_a_measured_effect(self):
        assert set(FIELD_EFFECT) == set(FIELD_BOUNDS)

    def test_every_effect_uses_a_known_direction(self):
        for field, efek in FIELD_EFFECT.items():
            assert efek["arah"] in DIRECTION_LABEL, field

    def test_neutral_label_matches_threshold(self):
        for field, efek in FIELD_EFFECT.items():
            if efek["arah"] == "netral":
                assert efek["dampak"] < AMBANG_EFFECT, field
            else:
                assert efek["dampak"] >= AMBANG_EFFECT, field

    def test_effect_covers_only_numeric_fields(self):
        for field in FIELD_EFFECT:
            assert field not in SELECT_OPTIONS, field

    def test_field_help_appends_direction(self):
        for field, efek in FIELD_EFFECT.items():
            teks = field_help(field)
            assert DIRECTION_LABEL[efek["arah"]] in teks, field
            # Deskripsi asli harus tetap utuh di depan anotasi arah.
            if field in FIELD_HELP:
                assert teks.startswith(FIELD_HELP[field]), field

    def test_field_help_without_effect_returns_plain_help(self):
        assert field_help("gender") == FIELD_HELP["gender"]
        assert field_help("code_module") == FIELD_HELP["code_module"]
        assert field_effect("gender") is None

    def test_effect_rows_sorted_by_importance_desc(self):
        rows = effect_rows()
        assert len(rows) == len(FIELD_EFFECT)
        penting = [r["Penting (%)"] for r in rows]
        assert penting == sorted(penting, reverse=True)

    def test_effect_rows_expose_table_columns(self):
        for row in effect_rows():
            assert set(row) == {"Field", "Arah nilai", "Perubahan risiko", "Penting (%)"}
            assert row["Arah nilai"] in DIRECTION_LABEL.values()


class TestRemovedFields:
    """`hari_terakhir_akses` dihapus karena sweep membuktikan efeknya nol."""

    def test_field_is_gone_from_form_config(self):
        for name, mapping in [
            ("FORM_DEFAULTS", FORM_DEFAULTS),
            ("FIELD_LABELS", FIELD_LABELS),
            ("FIELD_BOUNDS", FIELD_BOUNDS),
            ("FIELD_HELP", FIELD_HELP),
            ("FIELD_EFFECT", FIELD_EFFECT),
        ]:
            assert "hari_terakhir_akses" not in mapping, name

    def test_field_is_gone_from_presets_and_sections(self):
        assert "hari_terakhir_akses" not in CONTOH_BERISIKO
        assert "hari_terakhir_akses" not in CONTOH_TIDAK_BERISIKO
        semua_section = [f for _, fields in FORM_SECTIONS for f in fields]
        assert "hari_terakhir_akses" not in semua_section

    def test_no_form_field_is_left_without_model_effect(self):
        assert NON_MODEL_FORM_FIELDS == []

    def test_misleading_label_was_renamed(self):
        assert FIELD_LABELS["jarak_akses_terakhir"] == "Hari akses terakhir (relatif)"
        assert "Jarak akses terakhir" not in FIELD_LABELS.values()


class TestAssets:
    def test_every_declared_figure_exists(self):
        assert missing() == [], f"gambar hilang: {missing()}"

    def test_available_matches_figure_count(self):
        assert len(available()) == len(FIGURES)

    def test_assets_dir_exists(self):
        assert os.path.isdir(ASSETS_DIR)

    def test_each_figure_has_title_and_caption(self):
        for filename, (title, caption) in FIGURES.items():
            assert title.strip()
            assert caption.strip()
            assert os.path.exists(asset_path(filename))

    def test_asset_path_points_into_assets_dir(self):
        assert asset_path("x.png").startswith(ASSETS_DIR)
