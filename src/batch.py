"""
Modul batch — memproses banyak mahasiswa sekaligus dari DataFrame.

Fungsi-fungsi di sini murni (tidak menyentuh Streamlit) supaya bisa diuji
tanpa menjalankan aplikasi.
"""
import pandas as pd

from src.config import THRESHOLD
from src.form_config import (
    FIELD_BOUNDS, FIELD_LABELS, FORM_DEFAULTS, REQUIRED_INPUT_FIELDS,
)
from src.prediction import predict_students
from src.validation import validate_input

# Kolom yang wajib ada di CSV unggahan.
REQUIRED_COLUMNS = list(REQUIRED_INPUT_FIELDS)

# Batas baris per unggahan agar prediksi tidak memakan waktu terlalu lama.
MAX_BATCH_ROWS = 5000

RESULT_COLUMNS = [
    "kelas_prediksi",
    "label_prediksi",
    "probabilitas_berisiko",
    "probabilitas_tidak_berisiko",
]


def template_dataframe(n_rows: int = 3) -> pd.DataFrame:
    """Template CSV berisi kolom yang benar, contoh dari data default."""
    row = {field: FORM_DEFAULTS[field] for field in REQUIRED_COLUMNS}
    frame = pd.DataFrame([row] * max(1, n_rows))
    return frame[REQUIRED_COLUMNS]


def check_columns(df: pd.DataFrame) -> list[str]:
    """Kolom yang wajib ada tetapi tidak ditemukan di DataFrame."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return [f"Kolom wajib tidak ditemukan: {', '.join(missing)}"]
    return []


def coerce_types(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Ubah kolom numerik menjadi float. Kembalikan frame baru + daftar error."""
    errors = []
    out = df.copy()

    for field in REQUIRED_COLUMNS:
        if field not in out.columns:
            continue
        if field in FIELD_BOUNDS:
            converted = pd.to_numeric(out[field], errors="coerce")
            bad = converted.isna() & out[field].notna()
            if bad.any():
                contoh = out.loc[bad, field].astype(str).unique()[:3]
                errors.append(
                    f"Kolom '{field}' harus berupa angka. Nilai tidak valid: "
                    f"{', '.join(contoh)}{' ...' if bad.sum() > len(contoh) else ''}"
                )
            out[field] = converted
        else:
            out[field] = out[field].astype("string").str.strip()

    return out, errors


def validate_frame(
    df: pd.DataFrame,
    feature_ranges: dict | None = None,
    max_errors: int = 20,
    module_stats: dict | None = None,
) -> list[str]:
    """Validasi per baris. Kembalikan daftar error yang bisa ditampilkan."""
    errors: list[str] = []

    if df.empty:
        return ["File CSV tidak memiliki data (hanya header)."]

    coerced, type_errors = coerce_types(df)
    errors.extend(type_errors)
    if type_errors:
        return errors[:max_errors]

    if coerced.isna().any().any():
        for field in REQUIRED_COLUMNS:
            if field in coerced.columns and coerced[field].isna().any():
                count = int(coerced[field].isna().sum())
                errors.append(f"Kolom '{field}' kosong pada {count} baris.")

    for idx, row in coerced.iterrows():
        payload = {field: row[field] for field in REQUIRED_COLUMNS}
        _, row_errors = validate_input(payload, feature_ranges, module_stats)
        for message in row_errors:
            errors.append(f"Baris {idx + 1}: {message}")

    return errors[:max_errors]


def _valid_row_mask(
    df: pd.DataFrame,
    feature_ranges: dict | None,
    module_stats: dict | None = None,
) -> pd.Series:
    """Mask baris yang lolos validasi — dipakai agar prediksi tidak error."""
    mask = pd.Series(True, index=df.index)
    for idx, row in df.iterrows():
        payload = {field: row[field] for field in REQUIRED_COLUMNS}
        is_valid, _ = validate_input(payload, feature_ranges, module_stats)
        if not is_valid:
            mask.loc[idx] = False
    return mask


def predict_frame(
    df: pd.DataFrame,
    feature_ranges: dict | None = None,
    module_stats: dict | None = None,
) -> pd.DataFrame:
    """Tambahkan kolom hasil prediksi ke DataFrame input.

    Baris yang gagal validasi mendapat NaN pada kolom hasil, bukan exception.
    """
    coerced, _ = coerce_types(df)
    out = coerced.copy()

    for column in RESULT_COLUMNS:
        out[column] = pd.NA

    mask = _valid_row_mask(coerced, feature_ranges, module_stats)
    valid_idx = list(coerced.index[mask])
    if not valid_idx:
        return out

    rows = [{field: coerced.at[idx, field] for field in REQUIRED_COLUMNS}
            for idx in valid_idx]
    results = predict_students(rows)

    predictions = []
    for idx, result in zip(valid_idx, results):
        predictions.append((
            idx,
            result["prediction"],
            result["label"],
            result["probability_risk"],
            result["probability_not_risk"],
        ))

    pred_frame = pd.DataFrame(
        predictions,
        columns=[
            "idx", "kelas_prediksi", "label_prediksi",
            "probabilitas_berisiko", "probabilitas_tidak_berisiko",
        ],
    ).set_index("idx")

    for column in RESULT_COLUMNS:
        out.loc[pred_frame.index, column] = pred_frame[column]

    return out


def summarize(out: pd.DataFrame) -> dict:
    """Ringkasan hasil prediksi untuk ditampilkan sebagai metric."""
    total = len(out)
    valid = int(out["probabilitas_berisiko"].notna().sum())
    at_risk = int((out["kelas_prediksi"] == 0).sum())
    return {
        "total": total,
        "valid": valid,
        "invalid": total - valid,
        "at_risk": at_risk,
        "not_at_risk": valid - at_risk,
        "at_risk_pct": (at_risk / valid * 100) if valid else 0.0,
        "mean_risk": (
            float(out["probabilitas_berisiko"].dropna().mean()) if valid else float("nan")
        ),
        "threshold": THRESHOLD,
    }


def risk_by_group(out: pd.DataFrame, column: str, min_group: int = 1) -> pd.DataFrame:
    """Rata-rata probabilitas risiko per kategori, untuk ringkasan batch."""
    if column not in out.columns:
        return pd.DataFrame(columns=["jumlah", "berisiko", "risiko_rata"])

    grouped = out.groupby(column, dropna=False)["probabilitas_berisiko"].agg(
        jumlah="count",
        risiko_rata="mean",
    )
    at_risk = out.groupby(column, dropna=False)["kelas_prediksi"].apply(
        lambda s: (s == 0).sum()
    )
    grouped["berisiko"] = at_risk
    grouped = grouped[grouped["jumlah"] >= min_group].sort_values(
        "risiko_rata", ascending=False
    )
    grouped["risiko_rata"] = grouped["risiko_rata"] * 100
    return grouped.reset_index()


def download_frame(out: pd.DataFrame) -> pd.DataFrame:
    """Frame siap unduh: kolom hasil dibulatkan dan diurutkan."""
    download = out.copy()
    for column in ("probabilitas_berisiko", "probabilitas_tidak_berisiko"):
        if column in download.columns:
            download[column] = (download[column] * 100).round(2)
    return download


def column_help() -> pd.DataFrame:
    """Tabel referensi kolom untuk ditampilkan di UI."""
    rows = []
    for field in REQUIRED_COLUMNS:
        bounds = FIELD_BOUNDS.get(field)
        if bounds is None:
            rows.append({
                "kolom": field,
                "label": FIELD_LABELS.get(field, field),
                "tipe": "kategorikal",
                "rentang": "-",
            })
        else:
            rows.append({
                "kolom": field,
                "label": FIELD_LABELS.get(field, field),
                "tipe": "numerik",
                "rentang": f"{bounds[0]:g} s.d. {bounds[1]:g}",
            })
    return pd.DataFrame(rows)
