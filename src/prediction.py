"""
Modul prediksi — bangun matriks fitur, jalankan model EBM, klasifikasikan hasil.

Loader artefak tinggal di ``src.artifacts``. Modul ini fokus pada inference dan
pengukuran arah pengaruh field, dan tetap mengekspor loader tersebut untuk
kompatibilitas dengan kode/test lama.
"""
import numpy as np
import pandas as pd

from src.artifacts import (
    MODELS_DIR,
    artefak_hilang,
    artefak_siap,
    artifact_path,
    load_feature_ranges,
    load_label_encoders,
    load_model,
    load_module_stats,
    load_scaler,
)
from src.config import (
    AMBANG_EFFECT,
    FEATURE_ORDER,
    LABEL_MAP,
    NUMERIC_COLS,
    THRESHOLD,
)
from src.preprocessing import build_feature_row, encode_categoricals

__all__ = [
    "MODELS_DIR",
    "SWEEP_POINTS",
    "SMOOTH_WINDOW",
    "RASIO_MONOTON",
    "TOL_PUNCAK",
    "TOL_POSISI_PUNCAK",
    "artefak_hilang",
    "artefak_siap",
    "artifact_path",
    "classify_direction",
    "load_feature_ranges",
    "load_label_encoders",
    "load_model",
    "load_module_stats",
    "load_scaler",
    "measure_field_effect",
    "predict_student",
    "predict_students",
]


def _encode_frame(rows: list[dict], module_stats: dict | None) -> pd.DataFrame:
    """Bangun matriks fitur ter-scaling untuk satu atau lebih baris input."""
    encoders = load_label_encoders()
    scaler = load_scaler()

    rows_lengkap = [build_feature_row(row, module_stats) for row in rows]
    encoded = [encode_categoricals(row, encoders) for row in rows_lengkap]

    X_encoded = pd.DataFrame(encoded)[FEATURE_ORDER]
    X_scaled = X_encoded.copy()
    X_scaled[NUMERIC_COLS] = scaler.transform(X_encoded[NUMERIC_COLS])
    return X_scaled[FEATURE_ORDER]


def _classify(probability_risk: float) -> dict:
    """Terapkan threshold dan kembalikan hasil klasifikasi tanpa matriks fitur."""
    prediction = 0 if probability_risk >= THRESHOLD else 1
    return {
        "prediction": prediction,
        "label": LABEL_MAP[prediction],
        "probability_risk": probability_risk,
        "probability_not_risk": 1.0 - probability_risk,
        "threshold": THRESHOLD,
    }


def predict_student(raw_input: dict) -> dict:
    """Prediksi risiko mahasiswa dari input mentah. Mengembalikan dict hasil."""
    model = load_model()
    X_scaled = _encode_frame([raw_input], load_module_stats())
    probability_risk = float(model.predict_proba(X_scaled)[0][0])

    result = _classify(probability_risk)
    result["X_scaled"] = X_scaled
    return result


def predict_students(raw_inputs: list[dict]) -> list[dict]:
    """Prediksi banyak mahasiswa sekaligus. Satu panggilan model untuk semua baris."""
    if not raw_inputs:
        return []

    model = load_model()
    X_scaled = _encode_frame(raw_inputs, load_module_stats())
    probabilities = model.predict_proba(X_scaled)

    return [_classify(float(row[0])) for row in probabilities]


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

    ``field`` dijalankan dari ``low`` ke ``high`` dalam ``points`` langkah sama
    jarak, sementara field lain ditahan pada ``baseline``. Hasilnya:

        risiko_min / risiko_maks : nilai risiko terkecil dan terbesar
        rentang                   : risiko_maks - risiko_min, yaitu seberapa
                                    jauh risiko bergerak karena field ini saja
        arah                      : "naik_berisiko" / "naik_aman" /
                                    "risiko_puncak_tengah" / "tidak_monoton" /
                                    "netral"

    ``rentang`` sengaja dipakai, bukan selisih antara nilai ``low`` dan ``high``.
    Untuk field non-monoton keduanya jauh berbeda: field yang paling aman di
    tengah rentang punya selisih ujung yang kecil padahal risikonya bergerak
    jauh sekali di tengah-tengah.

    Arah ditentukan dari SELURUH kurva (lihat ``classify_direction``), bukan
    dari dua ujungnya saja, dan field yang risikonya tidak bergerak sama sekali
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
