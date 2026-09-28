"""
Modul prediksi — load artifacts, jalankan model EBM, hasilkan prediksi.
"""
import json
import os

import joblib
import pandas as pd
import streamlit as st

from src.config import FEATURE_ORDER, LABEL_MAP, NUMERIC_COLS, THRESHOLD
from src.preprocessing import build_feature_row, encode_categoricals

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")


def _path(name: str) -> str:
    return os.path.join(MODELS_DIR, name)


@st.cache_resource(show_spinner=False)
def load_model():
    return joblib.load(_path("04_final_model.pkl"))


@st.cache_resource(show_spinner=False)
def load_scaler():
    return joblib.load(_path("03_scaler.pkl"))


@st.cache_resource(show_spinner=False)
def load_label_encoders():
    return joblib.load(_path("label_encoders.pkl"))


@st.cache_data(show_spinner=False)
def load_module_stats():
    p = _path("module_stats.json")
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_feature_ranges():
    p = _path("feature_ranges.json")
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def artefak_siap() -> bool:
    return all(
        os.path.exists(_path(f))
        for f in ["04_final_model.pkl", "03_scaler.pkl", "label_encoders.pkl"]
    )


def _encode_frame(rows: list[dict], module_stats: dict | None) -> pd.DataFrame:
    """Bangun matriks fitur ter-scaling untuk satu atau lebih baris input."""
    model_encoders = load_label_encoders()
    scaler = load_scaler()

    rows_lengkap = [build_feature_row(row, module_stats) for row in rows]
    encoded = [encode_categoricals(row, model_encoders) for row in rows_lengkap]

    X_encoded = pd.DataFrame(encoded)[FEATURE_ORDER]
    X_scaled = X_encoded.copy()
    X_scaled[NUMERIC_COLS] = scaler.transform(X_encoded[NUMERIC_COLS])
    return X_scaled[FEATURE_ORDER]


def predict_student(raw_input: dict) -> dict:
    """Prediksi risiko mahasiswa dari input mentah. Mengembalikan dict hasil."""
    model = load_model()
    X_scaled = _encode_frame([raw_input], load_module_stats())

    proba = model.predict_proba(X_scaled)[0]
    probability_risk = float(proba[0])
    probability_not_risk = float(proba[1])

    prediction = 0 if probability_risk >= THRESHOLD else 1
    label = LABEL_MAP[prediction]

    return {
        "prediction": prediction,
        "label": label,
        "probability_risk": probability_risk,
        "probability_not_risk": probability_not_risk,
        "threshold": THRESHOLD,
        "X_scaled": X_scaled,
    }


def predict_students(raw_inputs: list[dict]) -> list[dict]:
    """Prediksi banyak mahasiswa sekaligus. Satu panggilan model untuk semua baris."""
    if not raw_inputs:
        return []

    model = load_model()
    X_scaled = _encode_frame(raw_inputs, load_module_stats())
    proba = model.predict_proba(X_scaled)

    results = []
    for row_proba in proba:
        probability_risk = float(row_proba[0])
        probability_not_risk = float(row_proba[1])
        prediction = 0 if probability_risk >= THRESHOLD else 1
        results.append({
            "prediction": prediction,
            "label": LABEL_MAP[prediction],
            "probability_risk": probability_risk,
            "probability_not_risk": probability_not_risk,
            "threshold": THRESHOLD,
        })
    return results


# Jumlah titik yang dipakai saat mengukur arah pengaruh sebuah field. Nilai ini
# dipakai ulang oleh test, supaya hasil ukur ulang benar-benar bisa dibandingkan
# dengan angka yang tersimpan di FIELD_EFFECT.
SWEEP_POINTS = 5


def measure_field_effect(
    field: str,
    low: float,
    high: float,
    baseline: dict,
    points: int = SWEEP_POINTS,
) -> dict:
    """Ukur arah dan besaran pengaruh satu field terhadap risiko.

    `field` dijankan dari `low` ke `high` dalam `points` langkah sama jarak,
    sementara field lain ditahan pada `baseline`. Hasilnya:

        risiko_min / risiko_maks : nilai risiko terkecil dan terbesar di sepang
        rentang                   : risiko_maks - risiko_min, yaitu seberapa jauh
                                   risiko bergerak karena field ini saja
        arah                      : "naik_berisiko" / "naik_aman" / "puncak_tengah"

    `rentang` sengaja dipakai, bukan selisih antara nilai `low` dan `high`.
    Untuk field non-monoton keduanya jauh berbeda: field yang paling aman di
    tengah rentang punya selisih ujung yang kecil padahal risikonya bergerak
    jauh sekali di tengah-tengah.
    """
    model = load_model()
    stats = load_module_stats()

    risks = []
    for i in range(points):
        nilai = low + (high - low) * i / (points - 1)
        baris = dict(baseline)
        baris[field] = nilai
        X = _encode_frame([baris], stats)
        risks.append(float(model.predict_proba(X)[0][0]))

    if risks[-1] > risks[0] and min(risks) == risks[0]:
        arah = "naik_berisiko"
    elif risks[-1] < risks[0] and min(risks) == risks[-1]:
        arah = "naik_aman"
    elif min(risks) in (risks[0], risks[-1]):
        arah = "puncak_ujung"
    else:
        arah = "puncak_tengah"

    return {
        "risiko_min": min(risks),
        "risiko_maks": max(risks),
        "rentang": max(risks) - min(risks),
        "arah": arah,
        "risiko_per_poin": risks,
    }