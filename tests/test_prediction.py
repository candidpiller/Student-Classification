"""Tests untuk modul prediction dan akses artefak model."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.artifacts import artefak_hilang, artefak_siap, artifact_path
from src.config import (
    ARTIFACT_MODULE_STATS,
    REQUIRED_ARTIFACT_FILES,
    THRESHOLD,
)


def test_threshold_value():
    assert THRESHOLD == 0.50


def test_threshold_logic():
    probability_risk = 0.60
    if probability_risk >= THRESHOLD:
        prediction = 0
    else:
        prediction = 1
    assert prediction == 0

    probability_risk = 0.30
    if probability_risk >= THRESHOLD:
        prediction = 0
    else:
        prediction = 1
    assert prediction == 1


def test_probability_range():
    prob_risk = 0.75
    prob_not_risk = 0.25
    assert 0 <= prob_risk <= 1
    assert 0 <= prob_not_risk <= 1
    assert abs(prob_risk + prob_not_risk - 1.0) < 1e-6


def test_artifacts_exist():
    for name in REQUIRED_ARTIFACT_FILES:
        assert artifact_path(name).is_file(), name
    assert artifact_path(ARTIFACT_MODULE_STATS).is_file()


def test_artifact_readiness_matches_inventory():
    assert artefak_siap()
    assert artefak_hilang() == []
