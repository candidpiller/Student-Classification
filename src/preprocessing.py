"""
Modul preprocessing — feature engineering, encoding, scaling.
Mereplikasi pipeline persis dari notebook pelatihan.
"""
import numpy as np
import pandas as pd

from src.config import (
    CATEGORICAL_COLS, CODE_MODULES, CODE_PRESENTATIONS, DEFAULT_CATEGORIES,
    FEATURE_ORDER, GLOBAL_PASS_RATE,
)


def hitung_fitur_turunan(row: dict) -> dict:
    """Menghitung fitur turunan + periode_puncak_aktivitas dari input mentah."""
    r = dict(row)

    total_klik = r["klik_awal"] + r["klik_tengah"] + r["klik_akhir"] + 1e-9

    r["click_per_day"] = r["total_click_events"] / (r["jumlah_hari_akses"] + 1)
    r["nilai_consistency"] = 1 / (r["std_nilai_assessment"] + 1)
    r["early_engagement"] = r["total_click_events"] / (r["durasi_pembelajaran_hari"] + 1)
    r["nilai_x_assessment"] = r["rata_rata_nilai_assessment"] * r["jumlah_assessment"]
    r["engagement_per_assessment"] = r["total_click_events"] / (r["jumlah_assessment"] + 1)
    r["tren_x_konsistensi"] = r["tren_klik"] * r["nilai_consistency"]
    r["rasio_klik_awal"] = r["klik_awal"] / total_klik
    r["rasio_klik_akhir"] = r["klik_akhir"] / total_klik

    klik_arr = [r["klik_awal"], r["klik_tengah"], r["klik_akhir"]]
    r["periode_puncak_aktivitas"] = int(np.argmax(klik_arr))

    return r


def presentation_pairs(module_stats: dict | None) -> dict[str, list[str]]:
    """Pasangan modul-presentasi yang benar-benar ada di data latih.

    Diturunkan dari kunci `presentation_pass_rate` di module_stats.json, bukan
    dari kombinasi silang CODE_MODULES x CODE_PRESENTATIONS, karena OULAD hanya
    membuka sebagian kombinasi itu. Kombinasi yang tidak ada di sini tidak pernah
    terjadi pada data nyata.
    """
    if not module_stats:
        return {module: list(CODE_PRESENTATIONS) for module in CODE_MODULES}

    rates = module_stats.get("presentation_pass_rate") or {}
    pairs: dict[str, list[str]] = {}
    for module in CODE_MODULES:
        available = [
            presentation for presentation in CODE_PRESENTATIONS
            if f"{module}_{presentation}" in rates
        ]
        pairs[module] = available or list(CODE_PRESENTATIONS)
    return pairs


def presentations_for(code_module: str, module_stats: dict | None) -> list[str]:
    """Presentasi yang valid untuk sebuah modul."""
    return presentation_pairs(module_stats).get(code_module, list(CODE_PRESENTATIONS))


def pair_is_valid(
    code_module: str,
    code_presentation: str,
    module_stats: dict | None,
) -> bool:
    """True bila kombinasi modul-presentasi benar-benar ada di data latih.

    Tanpa module_stats tidak ada yang bisa diverifikasi, jadi dianggap valid.
    """
    if not module_stats:
        return True
    return code_presentation in presentations_for(code_module, module_stats)


def hitung_skor_kesulitan(
    code_module: str,
    code_presentation: str,
    rata_rata_nilai_assessment: float,
    module_stats: dict | None,
) -> dict:
    """Menghitung 3 fitur difficulty dari module_stats.json."""
    default = GLOBAL_PASS_RATE
    if module_stats:
        default = float(module_stats.get("global_pass_rate", GLOBAL_PASS_RATE))

    if module_stats and code_module in module_stats.get("module_pass_rate", {}):
        skor_modul = 1 - module_stats["module_pass_rate"][code_module]
    else:
        skor_modul = 1 - default

    key = f"{code_module}_{code_presentation}"
    if module_stats and key in module_stats.get("presentation_pass_rate", {}):
        skor_pres = 1 - module_stats["presentation_pass_rate"][key]
    else:
        skor_pres = 1 - default

    skor_disesuaikan = rata_rata_nilai_assessment * (1 - skor_modul)

    return {
        "skor_kesulitan_modul": skor_modul,
        "skor_kesulitan_presentasi": skor_pres,
        "skor_disesuaikan_kesulitan": skor_disesuaikan,
    }


def encode_categoricals(row: dict, label_encoders: dict | None) -> dict:
    """Label encode kolom kategorikal menggunakan encoder dari training."""
    encoded = {}
    for col in FEATURE_ORDER:
        if col not in CATEGORICAL_COLS:
            encoded[col] = row[col]
            continue
        le = label_encoders.get(col) if label_encoders else None
        val = str(row[col])
        if le is not None and val in list(le.classes_):
            encoded[col] = int(le.transform([val])[0])
        else:
            cats = DEFAULT_CATEGORIES.get(col, [])
            encoded[col] = cats.index(val) if val in cats else 0
    return encoded


def build_feature_row(raw_input: dict, module_stats: dict | None) -> dict:
    """Satu fungsi untuk membangun baris fitur lengkap dari input mentah user."""
    row = hitung_fitur_turunan(raw_input)

    skor = hitung_skor_kesulitan(
        raw_input["code_module"],
        raw_input["code_presentation"],
        raw_input["rata_rata_nilai_assessment"],
        module_stats,
    )
    row.update(skor)

    return row


def bangun_dataframe_fitur(row_lengkap: dict) -> pd.DataFrame:
    """Susun satu baris fitur menjadi DataFrame dengan urutan kolom yang benar."""
    data = {k: [row_lengkap[k]] for k in FEATURE_ORDER}
    return pd.DataFrame(data)
