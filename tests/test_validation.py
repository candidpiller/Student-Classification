"""Tests untuk modul validation."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.validation import validate_input


def test_valid_input():
    data = {
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
    is_valid, errors = validate_input(data)
    assert is_valid
    assert len(errors) == 0


def test_missing_field():
    data = {"gender": "M"}
    is_valid, errors = validate_input(data)
    assert not is_valid
    assert len(errors) > 0


def test_invalid_category():
    data = {
        "gender": "X", "region": "London Region", "highest_education": "A Level or Equivalent",
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
    is_valid, errors = validate_input(data)
    assert not is_valid


def test_min_greater_than_max():
    data = {
        "gender": "M", "region": "London Region", "highest_education": "A Level or Equivalent",
        "imd_band": "20-30%", "age_band": "0-35", "disability": "N",
        "num_of_prev_attempts": 0, "studied_credits": 60, "code_module": "BBB",
        "code_presentation": "2014J", "rata_rata_sks_modul": 60,
        "jumlah_mahasiswa_presentasi": 500, "jumlah_assessment": 8,
        "rata_rata_nilai_assessment": 75.0, "std_nilai_assessment": 8.0,
        "min_nilai_assessment": 90.0, "max_nilai_assessment": 50.0,
        "jumlah_assessment_banked": 0, "total_click_events": 1500,
        "rata_rata_click_per_aktivitas": 5.0, "std_click_events": 10.0,
        "hari_pertama_akses": 0, "hari_terakhir_akses": 200,
        "jumlah_hari_akses": 90, "durasi_pembelajaran_hari": 200,
        "klik_awal": 500, "klik_tengah": 500, "klik_akhir": 500,
        "tren_klik": 1.0, "jarak_akses_terakhir": 20,
        "konsistensi_keterlibatan": 0.3, "kemiringan_klik_mingguan": 0.0,
    }
    is_valid, errors = validate_input(data)
    assert not is_valid
    assert any("minimum" in e.lower() for e in errors)


def test_negative_values():
    data = {
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
        "jumlah_hari_akses": -10, "durasi_pembelajaran_hari": 200,
        "klik_awal": 500, "klik_tengah": 500, "klik_akhir": 500,
        "tren_klik": 1.0, "jarak_akses_terakhir": 20,
        "konsistensi_keterlibatan": 0.3, "kemiringan_klik_mingguan": 0.0,
    }
    is_valid, errors = validate_input(data)
    assert not is_valid
    assert any(        "negatif" in e.lower() for e in errors)


def _valid_data(**overrides):
    data = {
        "gender": "M", "region": "London Region", "highest_education": "A Level or Equivalent",
        "imd_band": "20-30%", "age_band": "0-35", "disability": "N",
        "num_of_prev_attempts": 0, "studied_credits": 60, "code_module": "BBB",
        "code_presentation": "2014J", "rata_rata_sks_modul": 60,
        "jumlah_mahasiswa_presentasi": 500, "jumlah_assessment": 8.0,
        "rata_rata_nilai_assessment": 75.0, "std_nilai_assessment": 8.0,
        "min_nilai_assessment": 50.0, "max_nilai_assessment": 90.0,
        "jumlah_assessment_banked": 0.0, "total_click_events": 1500.0,
        "rata_rata_click_per_aktivitas": 5.0, "std_click_events": 10.0,
        "hari_pertama_akses": 0.0, "hari_terakhir_akses": 200.0,
        "jumlah_hari_akses": 90.0, "durasi_pembelajaran_hari": 200.0,
        "klik_awal": 500.0, "klik_tengah": 500.0, "klik_akhir": 500.0,
        "tren_klik": 1.0, "jarak_akses_terakhir": 20.0,
        "konsistensi_keterlibatan": 0.3, "kemiringan_klik_mingguan": 0.0,
    }
    data.update(overrides)
    return data


def test_unknown_code_module_rejected():
    is_valid, errors = validate_input(_valid_data(code_module="ZZZ"))
    assert not is_valid
    assert any("Kode modul" in e for e in errors)


def test_unknown_code_presentation_rejected():
    is_valid, errors = validate_input(_valid_data(code_presentation="9999Z"))
    assert not is_valid
    assert any("Kode presentasi" in e for e in errors)


def test_feature_ranges_nested_under_features_key_are_enforced():
    """feature_ranges.json menyimpan rentang di key 'features', bukan level atas."""
    ranges = {
        "dataset": "OULAD",
        "model": "Explainable Boosting Machine",
        "n_features": 40,
        "feature_names": ["studied_credits"],
        "features": {"studied_credits": {"type": "numeric", "min": 30, "max": 655}},
    }
    is_valid, errors = validate_input(_valid_data(), ranges)
    assert is_valid, errors

    is_valid, errors = validate_input(_valid_data(studied_credits=99999), ranges)
    assert not is_valid
    assert any("studied_credits" in e and "maksimum" in e for e in errors)

    is_valid, errors = validate_input(_valid_data(studied_credits=1), ranges)
    assert not is_valid
    assert any("studied_credits" in e and "minimum" in e for e in errors)


def test_feature_ranges_flat_format_still_supported():
    """Format lama (rentang langsung di level atas) tetap bisa dibaca."""
    ranges = {"studied_credits": {"min": 30, "max": 655}}
    is_valid, errors = validate_input(_valid_data(studied_credits=99999), ranges)
    assert not is_valid
    assert any("studied_credits" in e for e in errors)


def test_categorical_values_skipped_by_range_check():
    """Nilai kategorikal (string) tidak boleh dianggap pelanggaran rentang numerik."""
    ranges = {"features": {"gender": {"type": "numeric", "min": 0, "max": 1}}}
    is_valid, errors = validate_input(_valid_data(), ranges)
    assert is_valid, errors


def test_real_feature_ranges_file_is_consumed():
    """Pastikan file models/feature_ranges.json benar-benar terpakai validasi."""
    from src.prediction import load_feature_ranges

    ranges = load_feature_ranges()
    assert ranges is not None and "features" in ranges

    is_valid, errors = validate_input(_valid_data(), ranges)
    assert is_valid, errors

    is_valid, errors = validate_input(_valid_data(kemiringan_klik_mingguan=-9999.0), ranges)
    assert not is_valid
    assert any("kemiringan_klik_mingguan" in e for e in errors)
