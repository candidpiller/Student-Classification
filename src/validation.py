"""
Modul validasi input — memastikan semua data valid sebelum prediksi.
"""
import math

from src.config import (
    CATEGORICAL_COLS, CODE_MODULES, CODE_PRESENTATIONS, DEFAULT_CATEGORIES,
    REQUIRED_INPUT_FIELDS,
)
from src.preprocessing import pair_is_valid, presentations_for


def _numeric_ranges(feature_ranges: dict | None) -> dict:
    """Ambil tabel rentang numerik dari feature_ranges.json.

    File tersebut menyimpan metadata di level atas (dataset, model, target, ...)
    dan rentang tiap fitur di dalam key "features". Versi lama yang hanya
    menulis rentang langsung di level atas juga tetap didukung.
    """
    if not feature_ranges:
        return {}
    nested = feature_ranges.get("features")
    if isinstance(nested, dict):
        return nested
    return {
        field: rng
        for field, rng in feature_ranges.items()
        if isinstance(rng, dict) and ("min" in rng or "max" in rng)
    }


def validate_input(
    data: dict,
    feature_ranges: dict | None = None,
    module_stats: dict | None = None,
) -> tuple[bool, list[str]]:
    """Validasi input user. Returns (is_valid, list_of_errors)."""
    errors = []

    for field in REQUIRED_INPUT_FIELDS:
        if field not in data or data[field] is None:
            errors.append(f"Field '{field}' belum diisi.")
            continue
        val = data[field]
        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
            errors.append(f"Field '{field}' mengandung nilai tidak valid (NaN/Inf).")

    for col in CATEGORICAL_COLS:
        if col in data and col in DEFAULT_CATEGORIES:
            if data[col] not in DEFAULT_CATEGORIES[col]:
                errors.append(f"Nilai '{data[col]}' tidak valid untuk kolom '{col}'.")

    if "code_module" in data and data["code_module"] not in CODE_MODULES:
        errors.append(f"Kode modul '{data['code_module']}' tidak dikenal.")

    if "code_presentation" in data and data["code_presentation"] not in CODE_PRESENTATIONS:
        errors.append(f"Kode presentasi '{data['code_presentation']}' tidak dikenal.")
    elif module_stats and "code_module" in data and not pair_is_valid(
        data["code_module"], data["code_presentation"], module_stats
    ):
        valid = presentations_for(data["code_module"], module_stats)
        errors.append(
            f"Modul '{data['code_module']}' tidak pernah di buka dengan presentasi "
            f"'{data['code_presentation']}'. Presentasi yang tersedia: "
            f"{', '.join(valid)}."
        )

    if "min_nilai_assessment" in data and "max_nilai_assessment" in data:
        try:
            if float(data["min_nilai_assessment"]) > float(data["max_nilai_assessment"]):
                errors.append("Nilai minimum assessment tidak boleh lebih besar dari maksimum.")
        except (TypeError, ValueError):
            pass

    if "jumlah_hari_akses" in data:
        try:
            if float(data["jumlah_hari_akses"]) < 0:
                errors.append("Jumlah hari akses tidak boleh negatif.")
        except (TypeError, ValueError):
            pass

    if "durasi_pembelajaran_hari" in data:
        try:
            if float(data["durasi_pembelajaran_hari"]) < 0:
                errors.append("Durasi pembelajaran tidak boleh negatif.")
        except (TypeError, ValueError):
            pass

    for field, rng in _numeric_ranges(feature_ranges).items():
        if field not in data:
            continue
        try:
            val = float(data[field])
        except (TypeError, ValueError):
            continue
        if "min" in rng and val < rng["min"]:
            errors.append(f"Nilai '{field}' ({val}) di bawah minimum ({rng['min']}).")
        if "max" in rng and val > rng["max"]:
            errors.append(f"Nilai '{field}' ({val}) di atas maksimum ({rng['max']}).")

    return len(errors) == 0, errors
