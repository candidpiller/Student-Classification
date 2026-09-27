"""Tests untuk src/batch.py — template, validasi per baris, prediksi, ringkasan."""
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.batch import (
    MAX_BATCH_ROWS, REQUIRED_COLUMNS, check_columns, coerce_types, column_help,
    download_frame, predict_frame, risk_by_group, summarize, template_dataframe,
    validate_frame,
)
from src.form_config import (
    CONTOH_BERISIKO, CONTOH_TIDAK_BERISIKO, FORM_DEFAULTS, PRESETS,
)
from src.prediction import artefak_siap, load_feature_ranges, load_module_stats

needs_model = pytest.mark.skipif(
    not artefak_siap(), reason="artefak model tidak tersedia"
)


@pytest.fixture(scope="module")
def module_stats():
    return load_module_stats()


@pytest.fixture(scope="module")
def feature_ranges():
    return load_feature_ranges()


def frame_of(*presets):
    return pd.DataFrame([
        {field: preset[field] for field in REQUIRED_COLUMNS} for preset in presets
    ])


class TestTemplate:
    def test_template_covers_every_required_column(self):
        template = template_dataframe(3)

        assert list(template.columns) == REQUIRED_COLUMNS
        assert len(template) == 3
        assert check_columns(template) == []

    def test_template_uses_form_defaults(self):
        template = template_dataframe(1)

        for field in REQUIRED_COLUMNS:
            assert template.loc[0, field] == FORM_DEFAULTS[field]

    def test_template_is_valid_against_feature_ranges(self, feature_ranges):
        assert validate_frame(template_dataframe(1), feature_ranges) == []


class TestCheckColumns:
    def test_reports_missing_column(self):
        frame = template_dataframe(1).drop(columns=["region"])

        messages = check_columns(frame)

        assert len(messages) == 1
        assert "region" in messages[0]

    def test_complete_frame_has_no_messages(self):
        assert check_columns(template_dataframe(1)) == []


class TestCoerceTypes:
    def test_converts_numeric_strings_to_numbers(self):
        raw = pd.DataFrame([{field: "10" for field in REQUIRED_COLUMNS}])

        coerced, errors = coerce_types(raw)

        assert errors == []
        assert pd.api.types.is_numeric_dtype(coerced["studied_credits"])

    def test_converts_categories_to_string_dtype(self):
        raw = pd.DataFrame([{field: "10" for field in REQUIRED_COLUMNS}])

        coerced, _ = coerce_types(raw)

        assert str(coerced["gender"].dtype) == "string"

    def test_reports_non_numeric_values_in_numeric_column(self):
        raw = template_dataframe(1)
        raw["studied_credits"] = "bukan angka"

        coerced, errors = coerce_types(raw)

        assert len(errors) == 1
        assert "studied_credits" in errors[0]
        assert pd.isna(coerced["studied_credits"].iloc[0])

    def test_leaves_unknown_columns_untouched(self):
        raw = template_dataframe(1)
        raw["catatan"] = "bebas"

        coerced, errors = coerce_types(raw)

        assert errors == []
        assert coerced["catatan"].iloc[0] == "bebas"


class TestValidateFrame:
    def test_flags_value_above_maximum(self, feature_ranges):
        frame = frame_of(CONTOH_BERISIKO)
        frame.loc[0, "studied_credits"] = 99999

        messages = validate_frame(frame, feature_ranges)

        assert len(messages) == 1
        assert "studied_credits" in messages[0]
        assert messages[0].startswith("Baris 1")

    def test_flags_value_below_minimum(self, feature_ranges):
        frame = frame_of(CONTOH_BERISIKO)
        frame.loc[0, "studied_credits"] = 5

        messages = validate_frame(frame, feature_ranges)

        assert len(messages) == 1
        assert "di bawah minimum" in messages[0]

    def test_negative_value_reports_non_negative_rule(self, feature_ranges):
        frame = frame_of(CONTOH_BERISIKO)
        frame.loc[0, "jumlah_hari_akses"] = -5

        messages = validate_frame(frame, feature_ranges)

        assert any("tidak boleh negatif" in m for m in messages)

    def test_flags_invalid_category(self, feature_ranges):
        frame = frame_of(CONTOH_BERISIKO)
        frame.loc[0, "gender"] = "X"

        messages = validate_frame(frame, feature_ranges)

        assert len(messages) == 1
        assert "gender" in messages[0]

    def test_reports_one_based_row_numbers(self, feature_ranges):
        frame = frame_of(CONTOH_BERISIKO, CONTOH_BERISIKO)
        frame.loc[1, "studied_credits"] = 99999

        messages = validate_frame(frame, feature_ranges)

        assert len(messages) == 1
        assert messages[0].startswith("Baris 2")

    def test_empty_frame_is_rejected(self, feature_ranges):
        assert validate_frame(pd.DataFrame(columns=REQUIRED_COLUMNS), feature_ranges)

    def test_impossible_module_presentation_pair_is_rejected(
        self, feature_ranges, module_stats
    ):
        """CSV dengan kombinasi modul-presentasi yang tidak pernah ada harus ditolak."""
        frame = frame_of(CONTOH_BERISIKO)
        frame.loc[0, "code_module"] = "CCC"
        frame.loc[0, "code_presentation"] = "2013B"

        messages = validate_frame(frame, feature_ranges, module_stats=module_stats)

        assert any("CCC" in m and "2013B" in m for m in messages)

    def test_error_list_is_capped(self, feature_ranges):
        frame = frame_of(*([CONTOH_BERISIKO] * 40))
        frame["studied_credits"] = 99999

        assert len(validate_frame(frame, feature_ranges, max_errors=5)) == 5


class TestPresetRanges:
    """Regresi: nilai preset harus valid terhadap rentang data latih."""

    @pytest.mark.parametrize("name", list(PRESETS))
    def test_preset_is_valid(self, feature_ranges, name):
        assert validate_frame(frame_of(PRESETS[name]), feature_ranges) == []

    def test_all_numeric_preset_values_inside_ranges(self, feature_ranges):
        ranges = feature_ranges["features"]

        for name, values in PRESETS.items():
            for field, value in values.items():
                if field not in ranges or not isinstance(value, (int, float)):
                    continue
                low, high = ranges[field]["min"], ranges[field]["max"]
                assert low <= value <= high, (
                    f"{name}.{field} = {value} di luar [{low}, {high}]"
                )


@needs_model
class TestPredictFrame:
    def test_labels_known_presets(self, feature_ranges, module_stats):
        output = predict_frame(
            frame_of(CONTOH_BERISIKO, CONTOH_TIDAK_BERISIKO),
            feature_ranges,
            module_stats,
        )

        assert list(output["label_prediksi"]) == ["Berisiko", "Tidak Berisiko"]
        assert output["probabilitas_berisiko"].iloc[0] > 0.9
        assert output["probabilitas_berisiko"].iloc[1] < 0.5

    def test_impossible_pair_row_is_skipped(self, feature_ranges, module_stats):
        frame = frame_of(CONTOH_BERISIKO, CONTOH_TIDAK_BERISIKO)
        frame.loc[0, "code_module"] = "CCC"
        frame.loc[0, "code_presentation"] = "2013B"

        output = predict_frame(frame, feature_ranges, module_stats)

        assert pd.isna(output["probabilitas_berisiko"].iloc[0])
        assert output["label_prediksi"].iloc[1] == "Tidak Berisiko"

    def test_probabilities_sum_to_one(self, feature_ranges):
        output = predict_frame(frame_of(CONTOH_TIDAK_BERISIKO), feature_ranges)

        total = (
            output["probabilitas_berisiko"].iloc[0]
            + output["probabilitas_tidak_berisiko"].iloc[0]
        )
        assert total == pytest.approx(1.0, abs=1e-9)

    def test_keeps_original_columns(self, feature_ranges):
        output = predict_frame(frame_of(CONTOH_BERISIKO), feature_ranges)

        for field in REQUIRED_COLUMNS:
            assert field in output.columns

    def test_invalid_row_gets_missing_result_not_exception(self, feature_ranges):
        frame = frame_of(CONTOH_BERISIKO, CONTOH_TIDAK_BERISIKO)
        frame.loc[0, "studied_credits"] = 99999

        output = predict_frame(frame, feature_ranges)

        assert pd.isna(output["probabilitas_berisiko"].iloc[0])
        assert output["label_prediksi"].iloc[1] == "Tidak Berisiko"

    def test_fully_invalid_frame_returns_all_missing(self, feature_ranges):
        frame = frame_of(CONTOH_BERISIKO)
        frame["studied_credits"] = 99999

        output = predict_frame(frame, feature_ranges)

        assert output["probabilitas_berisiko"].isna().all()


@needs_model
class TestSummarize:
    def test_counts_split_correctly(self, feature_ranges):
        output = predict_frame(
            frame_of(CONTOH_BERISIKO, CONTOH_TIDAK_BERISIKO), feature_ranges
        )

        stats = summarize(output)

        assert stats["total"] == 2
        assert stats["valid"] == 2
        assert stats["invalid"] == 0
        assert stats["at_risk"] == 1
        assert stats["not_at_risk"] == 1
        assert stats["at_risk_pct"] == 50.0

    def test_invalid_rows_counted_separately(self, feature_ranges):
        frame = frame_of(CONTOH_BERISIKO, CONTOH_TIDAK_BERISIKO)
        frame.loc[0, "studied_credits"] = 99999

        stats = summarize(predict_frame(frame, feature_ranges))

        assert stats["valid"] == 1
        assert stats["invalid"] == 1
        assert stats["at_risk"] == 0
        assert stats["not_at_risk"] == 1

    def test_fully_invalid_frame_is_safe(self, feature_ranges):
        frame = frame_of(CONTOH_BERISIKO)
        frame.loc[0, "studied_credits"] = 99999

        stats = summarize(predict_frame(frame, feature_ranges))

        assert stats["valid"] == 0
        assert stats["at_risk"] == 0
        assert stats["at_risk_pct"] == 0.0
        assert pd.isna(stats["mean_risk"])

    def test_threshold_is_reported(self, feature_ranges):
        stats = summarize(predict_frame(frame_of(CONTOH_BERISIKO), feature_ranges))

        assert stats["threshold"] == 0.5


@needs_model
class TestRiskByGroup:
    def test_counts_only_valid_rows(self, feature_ranges):
        frame = frame_of(CONTOH_BERISIKO, CONTOH_TIDAK_BERISIKO, CONTOH_BERISIKO)
        frame.loc[2, "studied_credits"] = 99999

        grouped = risk_by_group(
            predict_frame(frame, feature_ranges), "code_module"
        ).set_index("code_module")

        assert grouped.loc["CCC", "jumlah"] == 1
        assert grouped.loc["CCC", "berisiko"] == 1
        assert grouped.loc["AAA", "jumlah"] == 1
        assert grouped.loc["AAA", "berisiko"] == 0

    def test_mean_is_reported_in_percent(self, feature_ranges):
        grouped = risk_by_group(
            predict_frame(frame_of(CONTOH_BERISIKO), feature_ranges), "code_module"
        )

        assert grouped["risiko_rata"].iloc[0] == pytest.approx(100.0, abs=0.01)

    def test_unknown_column_returns_empty(self, feature_ranges):
        output = predict_frame(frame_of(CONTOH_BERISIKO), feature_ranges)

        assert risk_by_group(output, "kolom_tidak_ada").empty


class TestDownloadFrame:
    def test_probabilities_become_percentages(self):
        output = pd.DataFrame({
            "probabilitas_berisiko": [0.25, 0.75],
            "probabilitas_tidak_berisiko": [0.75, 0.25],
        })

        result = download_frame(output)

        assert list(result["probabilitas_berisiko"]) == [25.0, 75.0]
        assert list(result["probabilitas_tidak_berisiko"]) == [75.0, 25.0]

    def test_leaves_input_columns_untouched(self):
        output = pd.DataFrame({"gender": ["M", "F"]})

        result = download_frame(output)

        assert list(result["gender"]) == ["M", "F"]


class TestColumnHelp:
    def test_documents_every_required_column(self):
        help_frame = column_help()

        assert list(help_frame.columns) == ["kolom", "label", "tipe", "rentang"]
        assert list(help_frame["kolom"]) == REQUIRED_COLUMNS

    def test_marks_categorical_and_numeric_correctly(self):
        help_frame = column_help().set_index("kolom")

        assert help_frame.loc["gender", "tipe"] == "kategorikal"
        assert help_frame.loc["gender", "rentang"] == "-"
        assert help_frame.loc["studied_credits", "tipe"] == "numerik"
        assert help_frame.loc["studied_credits", "rentang"] == "30 s.d. 655"

    def test_every_column_has_a_label(self):
        assert column_help()["label"].str.len().gt(0).all()


def test_batch_limits_are_sane():
    assert MAX_BATCH_ROWS > 0
    assert REQUIRED_COLUMNS
    assert set(REQUIRED_COLUMNS).issubset(FORM_DEFAULTS)
