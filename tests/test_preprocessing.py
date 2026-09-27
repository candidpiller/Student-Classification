"""Tests untuk modul preprocessing."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config import FEATURE_ORDER, CATEGORICAL_COLS
from src.preprocessing import build_feature_row, hitung_fitur_turunan, hitung_skor_kesulitan, encode_categoricals

RAW_EXAMPLE = {
    "gender": "M", "region": "London Region", "highest_education": "A Level or Equivalent",
    "imd_band": "20-30%", "age_band": "0-35", "disability": "N",
    "num_of_prev_attempts": 0, "studied_credits": 60, "code_module": "BBB",
    "code_presentation": "2014J", "rata_rata_sks_modul": 60,
    "jumlah_mahasiswa_presentasi": 500, "jumlah_assessment": 8,
    "rata_rata_nilai_assessment": 75.0, "std_nilai_assessment": 8.0,
    "min_nilai_assessment": 50.0, "max_nilai_assessment": 90.0,
    "jumlah_assessment_banked": 0, "total_click_events": 1500,
    "rata_rata_click_per_aktivitas": 5.0, "std_click_events": 10.0,
    "hari_pertama_akses": 0, "hari_terakhir_akses": 200,
    "jumlah_hari_akses": 90, "durasi_pembelajaran_hari": 200,
    "klik_awal": 500, "klik_tengah": 500, "klik_akhir": 500,
    "tren_klik": 1.0, "jarak_akses_terakhir": 20,
    "konsistensi_keterlibatan": 0.3, "kemiringan_klik_mingguan": 0.0,
}


def test_hitung_fitur_turunan():
    row = {
        "total_click_events": 1500, "jumlah_hari_akses": 90,
        "std_nilai_assessment": 8.0, "durasi_pembelajaran_hari": 200,
        "max_nilai_assessment": 90.0, "min_nilai_assessment": 50.0,
        "rata_rata_nilai_assessment": 75.0, "jumlah_assessment": 8,
        "klik_awal": 500, "klik_tengah": 500, "klik_akhir": 500,
        "tren_klik": 1.0, "std_click_events": 10.0,
    }
    result = hitung_fitur_turunan(row)

    assert "click_per_day" in result
    assert "nilai_consistency" in result
    assert "early_engagement" in result
    assert "nilai_x_assessment" in result
    assert "engagement_per_assessment" in result
    assert "tren_x_konsistensi" in result
    assert "periode_puncak_aktivitas" in result

    assert result["click_per_day"] == 1500 / 91
    assert result["nilai_x_assessment"] == 75.0 * 8
    assert result["periode_puncak_aktivitas"] == 0


def test_hitung_skor_kesulitan_with_stats():
    module_stats = {
        "module_pass_rate": {"AAA": 0.71, "BBB": 0.47},
        "presentation_pass_rate": {"AAA_2013J": 0.72, "BBB_2014J": 0.50},
    }
    result = hitung_skor_kesulitan("AAA", "2013J", 75.0, module_stats)
    assert abs(result["skor_kesulitan_modul"] - (1 - 0.71)) < 1e-6
    assert abs(result["skor_kesulitan_presentasi"] - (1 - 0.72)) < 1e-6
    assert abs(result["skor_disesuaikan_kesulitan"] - (75.0 * 0.71)) < 1e-6


def test_hitung_skor_kesulitan_without_stats():
    result = hitung_skor_kesulitan("ZZZ", "9999", 50.0, None)
    assert abs(result["skor_kesulitan_modul"] - 0.528) < 1e-3


def test_encode_categoricals():
    full_row = build_feature_row(RAW_EXAMPLE, None)
    result = encode_categoricals(full_row, None)
    assert isinstance(result["gender"], int)
    assert isinstance(result["region"], int)
    assert result["num_of_prev_attempts"] == 0
    assert len(result) == len(FEATURE_ORDER)


def test_feature_order_length():
    assert len(FEATURE_ORDER) == 40


def test_feature_order_categorical_count():
    cat_in_order = [c for c in FEATURE_ORDER if c in CATEGORICAL_COLS]
    assert len(cat_in_order) == 6


def test_feature_order_numeric_count():
    num_in_order = [c for c in FEATURE_ORDER if c not in CATEGORICAL_COLS]
    assert len(num_in_order) == 34