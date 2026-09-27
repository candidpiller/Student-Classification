"""Tests untuk src/explanation.py — local explanation dan global importance."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.explanation import get_global_importance, get_local_explanation
from src.form_config import CONTOH_BERISIKO
from src.prediction import artefak_siap, predict_student

pytestmark = pytest.mark.skipif(
    not artefak_siap(), reason="artefak model tidak tersedia"
)


@pytest.fixture(scope="module")
def risky_prediction():
    return predict_student(CONTOH_BERISIKO)


class TestLocalExplanation:
    def test_returns_top_features(self, risky_prediction):
        explanation = get_local_explanation(
            risky_prediction["X_scaled"], risky_prediction["prediction"]
        )

        assert 0 < len(explanation) <= 10
        assert all({"feature", "score", "direction"} <= set(e) for e in explanation)

    def test_scores_are_sorted_by_magnitude(self, risky_prediction):
        explanation = get_local_explanation(
            risky_prediction["X_scaled"], risky_prediction["prediction"]
        )
        magnitudes = [abs(e["score"]) for e in explanation]

        assert magnitudes == sorted(magnitudes, reverse=True)

    def test_direction_is_readable(self, risky_prediction):
        explanation = get_local_explanation(
            risky_prediction["X_scaled"], risky_prediction["prediction"]
        )

        for item in explanation:
            assert isinstance(item["direction"], str)
            assert item["direction"].strip()

    def test_bad_input_returns_empty_list(self):
        assert get_local_explanation(None, 0) == []


class TestGlobalImportance:
    def test_covers_every_model_feature(self):
        from src.config import FEATURE_ORDER

        importance = get_global_importance()

        assert set(importance["fitur"]) == set(FEATURE_ORDER)

    def test_percentages_sum_to_about_one_hundred(self):
        total = get_global_importance()["penting"].sum()

        assert total == pytest.approx(100.0, abs=0.1)

    def test_is_sorted_descending(self):
        importance = get_global_importance()

        values = importance["penting"].tolist()
        assert values == sorted(values, reverse=True)

    def test_top_n_limits_rows(self):
        assert len(get_global_importance(5)) == 5

    def test_top_feature_is_jarak_akses_terakhir(self):
        """Regresi: help text menyebut fitur ini sebagai yang paling berpengaruh."""
        importance = get_global_importance(1)

        assert importance["fitur"].iloc[0] == "jarak_akses_terakhir"

    def test_no_negative_percentages(self):
        assert get_global_importance()["penting"].ge(0).all()
