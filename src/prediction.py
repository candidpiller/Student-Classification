"""
Modul prediksi — load artifacts, jalankan model EBM, hasilkan prediksi.
"""
import json
import os

import joblib
import numpy as np
import pandas as pd
import streamlit as st

from src.config import (
    AMBANG_EFFECT, FEATURE_ORDER, LABEL_MAP, NUMERIC_COLS, THRESHOLD,
)
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
#
# Lima titik (lama) terlalu sedikit: EBM menghasilkan kurva anak tangga, jadi
# lima titik sering hanya memotong puncak atau lembah dan membuat kurva yang
# sebenarnya berayun terlihat monoton. Dua puluh satu titik cukup untuk melihat
# bentuk kurvanya.
SWEEP_POINTS = 21

# Lebar jendela perata-rata bergerak. Satu titik ekstrem di ujung rentang
# tidak boleh sendirian menentukan arah.
SMOOTH_WINDOW = 3

# Ambang rasio monoton: besar dari perubahan absolut kurva yang searah dengan
# perubahan dari ujung ke ujung. 1.0 = benar-benar monoton, 0 = bolak-balik
# penuh. Di bawah 0.85 kurva dianggap naik-turun, bukan aturan bersih.
RASIO_MONOTON = 0.85

# Selisih minimum (fraksi dari rentang) agar puncak kurva boleh disebut
# "di tengah rentang".
TOL_PUNCAK = 0.10

# Seberapa jauh dari titik tengah puncak boleh berada, dinormalisasi ke 0..1.
# 0.5 berarti puncak masih dianggap di tengah rentang.
TOL_POSISI_PUNCAK = 0.5


def _haluskan(nilai: list[float], window: int) -> np.ndarray:
    """Rata-rata bergerak dengan tepi dirata. Menembus noise satu titik."""
    arr = np.asarray(nilai, dtype=float)
    if window <= 1 or arr.size < window:
        return arr
    pad = window // 2
    tepi = np.concatenate([np.full(pad, arr[0]), arr, np.full(pad, arr[-1])])
    return np.convolve(tepi, np.ones(window) / window, mode="valid")


def _rasio_monoton(halus: np.ndarray) -> float:
    """Seberapa konsisten arah kurva: 1 monoton naik, -1 monoton turun."""
    diff = np.diff(halus)
    total = float(np.abs(diff).sum())
    if total <= 0:
        return 0.0
    return float((halus[-1] - halus[0]) / total)


def classify_direction(risks: list[float], rentang: float) -> str:
    """Tentukan arah pengaruh dari kurva risiko, bukan dari dua ujung saja.

    Versi lama hanya membandingkan nilai pertama dan terakhir, sehingga kurva
    yang berayun di tengah tetap diberi label "Naik = lebih berisiko" atau
    "Naik = lebih aman". Padahal kalau pengguna menggeser slider ke arah yang
    diklaim menaikkan risiko, model bisa justru menurunkan risiko di sana.

    Aturan baru:
        rentang < AMBANG_EFFECT  -> "netral" (efek terlalu kecil untuk
                                    disebut berarah)
        kurva monoton naik/turun  -> "naik_berisiko" / "naik_aman"
        puncak di tengah rentang   -> "risiko_puncak_tengah"
        lainnya                   -> "tidak_monoton"
    """
    if rentang < AMBANG_EFFECT:
        return "netral"

    halus = _haluskan(risks, SMOOTH_WINDOW)
    rasio = _rasio_monoton(halus)
    if rasio >= RASIO_MONOTON:
        return "naik_berisiko"
    if rasio <= -RASIO_MONOTON:
        return "naik_aman"

    # Puncak di tengah rentang: titik tertinggi kurva ada di bagian tengah
    # dan jelas lebih tinggi daripada kedua ujung.
    #
    # Puncak sering berupa plat datar (EBM menghasilkan kurva anak tangga),
    # jadi posisinya diambil dari titik tengah plat itu. Kalau hanya dipakai
    # indeks pertama yang menyentuh nilai maksimum, puncak simetris selalu
    # dianggap di sebelah kiri tengah dan salah dilaporkan sebagai
    # "tidak monoton".
    n = halus.size
    maks = float(halus.max())
    datar = np.flatnonzero(halus >= maks - 1e-9)
    puncak = int(round(float(datar.mean())))
    jarak_puncak = abs(puncak - (n - 1) / 2) / max((n - 1) / 2, 1)
    ujung = max(float(halus[0]), float(halus[-1]))
    if (
        jarak_puncak <= TOL_POSISI_PUNCAK
        and float(halus[puncak]) - ujung > TOL_PUNCAK * rentang
    ):
        return "risiko_puncak_tengah"
    return "tidak_monoton"


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
        arah                      : "naik_berisiko" / "naik_aman" /
                                   "risiko_puncak_tengah" / "tidak_monoton" /
                                   "netral"

    `rentang` sengaja dipakai, bukan selisih antara nilai `low` dan `high`.
    Untuk field non-monoton keduanya jauh berbeda: field yang paling aman di
    tengah rentang punya selisih ujung yang kecil padahal risikonya bergerak
    jauh sekali di tengah-tengah.

    Arah ditentukan dari SELURUH kurva (lihat `classify_direction`), bukan dari
    dua ujungnya saja, dan field yang risikonya tidak bergerak sama sekali
    ("netral") dilaporkan apa adanya.
    """
    model = load_model()
    stats = load_module_stats()

    baris = []
    for i in range(points):
        nilai = low + (high - low) * i / (points - 1)
        row = dict(baseline)
        row[field] = nilai
        baris.append(row)

    X = _encode_frame(baris, stats)
    risks = [float(p) for p in model.predict_proba(X)[:, 0]]

    rentang = max(risks) - min(risks)

    return {
        "risiko_min": min(risks),
        "risiko_maks": max(risks),
        "rentang": rentang,
        "arah": classify_direction(risks, rentang),
        "risiko_per_poin": risks,
    }
