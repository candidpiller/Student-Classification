"""Test untuk pasangan modul-presentasi.

OULAD hanya membuka sebagian kombinasi modul x presentasi. Kombinasi yang tidak
pernah ada tidak boleh masuk ke model, karena skor kesulitannya akan jatuh ke
fallback global dan jadi tidak informatif.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config import CODE_MODULES, CODE_PRESENTATIONS
from src.form_config import CONTOH_BERISIKO, CONTOH_TIDAK_BERISIKO, FORM_DEFAULTS, PRESETS
from src.prediction import load_feature_ranges, load_module_stats
from src.preprocessing import pair_is_valid, presentation_pairs, presentations_for
from src.validation import validate_input


@pytest.fixture(scope="module")
def module_stats():
    return load_module_stats()


@pytest.fixture(scope="module")
def feature_ranges():
    return load_feature_ranges()


def key(module, presentation):
    return f"{module}_{presentation}"


class TestPresentationPairs:
    def test_covers_every_module(self, module_stats):
        assert set(presentation_pairs(module_stats)) == set(CODE_MODULES)

    def test_only_lists_presentations_that_exist(self, module_stats):
        rates = module_stats["presentation_pass_rate"]
        pairs = presentation_pairs(module_stats)

        for module, presentations in pairs.items():
            for presentation in presentations:
                assert key(module, presentation) in rates, (
                    f"{key(module, presentation)} tidak ada di module_stats.json"
                )

    def test_fewer_pairs_than_full_cross_product(self, module_stats):
        """Penanda bahwa OULAD memang tidak membuka semua kombinasi."""
        total = sum(len(v) for v in presentation_pairs(module_stats).values())

        assert total < len(CODE_MODULES) * len(CODE_PRESENTATIONS)
        assert total == len(module_stats["presentation_pass_rate"])

    def test_known_modules_expose_expected_presentations(self, module_stats):
        assert presentations_for("AAA", module_stats) == ["2013J", "2014J"]
        assert presentations_for("CCC", module_stats) == ["2014B", "2014J"]
        assert presentations_for("BBB", module_stats) == CODE_PRESENTATIONS

    def test_falls_back_to_all_presentations_without_stats(self):
        assert presentations_for("AAA", None) == CODE_PRESENTATIONS

    def test_unknown_module_returns_all_presentations(self, module_stats):
        assert presentations_for("ZZZ", module_stats) == CODE_PRESENTATIONS


class TestPairIsValid:
    def test_real_pairs_are_valid(self, module_stats):
        assert pair_is_valid("AAA", "2013J", module_stats)
        assert pair_is_valid("CCC", "2014B", module_stats)

    def test_impossible_pairs_are_invalid(self, module_stats):
        assert not pair_is_valid("CCC", "2013B", module_stats)
        assert not pair_is_valid("AAA", "2013B", module_stats)
        assert not pair_is_valid("GGG", "2013B", module_stats)

    def test_missing_stats_cannot_reject_anything(self):
        assert pair_is_valid("CCC", "2013B", None)


class TestValidateInputRejectsImpossiblePair:
    def test_impossible_pair_is_rejected(self, feature_ranges, module_stats):
        data = {**FORM_DEFAULTS, "code_module": "CCC", "code_presentation": "2013B"}

        is_valid, errors = validate_input(data, feature_ranges, module_stats)

        assert not is_valid
        assert any("CCC" in e and "2013B" in e for e in errors)

    def test_error_lists_available_presentations(self, feature_ranges, module_stats):
        data = {**FORM_DEFAULTS, "code_module": "CCC", "code_presentation": "2013B"}

        _, errors = validate_input(data, feature_ranges, module_stats)

        assert any("2014B" in e and "2014J" in e for e in errors)

    def test_real_pair_passes(self, feature_ranges, module_stats):
        data = {**FORM_DEFAULTS, "code_module": "CCC", "code_presentation": "2014B"}

        is_valid, errors = validate_input(data, feature_ranges, module_stats)

        assert is_valid, errors

    def test_skipped_when_module_stats_absent(self, feature_ranges):
        data = {**FORM_DEFAULTS, "code_module": "CCC", "code_presentation": "2013B"}

        is_valid, errors = validate_input(data, feature_ranges)

        assert is_valid, errors


class TestPresetsUseRealPairs:
    """Regresi: default dan preset pernah memakai kombinasi yang tidak ada."""

    @pytest.mark.parametrize("name", sorted(PRESETS))
    def test_preset_pair_exists(self, module_stats, name):
        preset = PRESETS[name]

        assert pair_is_valid(
            preset["code_module"], preset["code_presentation"], module_stats
        ), (
            f"preset {name!r} memakai {key(preset['code_module'], preset['code_presentation'])} "
            "yang tidak pernah ada di OULAD"
        )

    def test_named_presets_are_valid(self, module_stats):
        for preset in (CONTOH_BERISIKO, CONTOH_TIDAK_BERISIKO):
            assert pair_is_valid(
                preset["code_module"], preset["code_presentation"], module_stats
            )

    @pytest.mark.parametrize("name", sorted(PRESETS))
    def test_preset_passes_full_validation(self, feature_ranges, module_stats, name):
        is_valid, errors = validate_input(PRESETS[name], feature_ranges, module_stats)

        assert is_valid, errors
