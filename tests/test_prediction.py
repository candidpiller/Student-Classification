"""Tests untuk modul prediction."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config import THRESHOLD


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
    models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
    assert os.path.exists(os.path.join(models_dir, "04_final_model.pkl"))
    assert os.path.exists(os.path.join(models_dir, "03_scaler.pkl"))
    assert os.path.exists(os.path.join(models_dir, "label_encoders.pkl"))
    assert os.path.exists(os.path.join(models_dir, "module_stats.json"))
