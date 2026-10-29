"""
Akses artefak model — path, status ketersediaan, dan loader yang di-cache.

Modul ini satu-satunya tempat yang tahu nama file artefak. Modul lain memakai
konstanta dari ``src.config`` atau fungsi di sini, sehingga mengganti nama file
model tidak perlu menyentuh halaman, test, dan logika prediksi.
"""
import json
from pathlib import Path

import joblib
import streamlit as st

from src.config import (
    ARTIFACT_FEATURE_RANGES,
    ARTIFACT_LABEL_ENCODERS,
    ARTIFACT_MODEL,
    ARTIFACT_MODULE_STATS,
    ARTIFACT_SCALER,
    REQUIRED_ARTIFACT_FILES,
)

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


def artifact_path(name: str) -> Path:
    """Path lengkap sebuah artefak di folder ``models/``."""
    return MODELS_DIR / name


def artefak_siap() -> bool:
    """True bila semua artefak wajib untuk inference tersedia."""
    return all(artifact_path(name).is_file() for name in REQUIRED_ARTIFACT_FILES)


def artefak_hilang() -> list[str]:
    """Nama artefak wajib yang belum ada di folder ``models/``."""
    return [name for name in REQUIRED_ARTIFACT_FILES if not artifact_path(name).is_file()]


@st.cache_resource(show_spinner=False)
def load_model():
    return joblib.load(artifact_path(ARTIFACT_MODEL))


@st.cache_resource(show_spinner=False)
def load_scaler():
    return joblib.load(artifact_path(ARTIFACT_SCALER))


@st.cache_resource(show_spinner=False)
def load_label_encoders():
    return joblib.load(artifact_path(ARTIFACT_LABEL_ENCODERS))


@st.cache_data(show_spinner=False)
def load_module_stats():
    path = artifact_path(ARTIFACT_MODULE_STATS)
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


@st.cache_data(show_spinner=False)
def load_feature_ranges():
    path = artifact_path(ARTIFACT_FEATURE_RANGES)
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def artifact_inventory() -> list[dict]:
    """Daftar artefak yang benar-benar ada, lengkap dengan ukurannya."""
    if not MODELS_DIR.is_dir():
        return []
    return [
        {
            "File": f"`models/{path.name}`",
            "Ukuran": f"{path.stat().st_size / 1024:,.1f} KB",
        }
        for path in sorted(MODELS_DIR.iterdir())
        if path.is_file()
    ]
