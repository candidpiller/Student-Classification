"""
Modul assets — lokasi gambar statis hasil notebook beserta deskripsinya.
"""
import os

ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets"
)

# name file -> (judul, keterangan)
# Hanya gambar yang benar-benar dirender di aplikasi yang didaftarkan di sini.
FIGURES = {
    "fig_kualitas_data_sintetis.png": (
        "Kualitas data sintetis",
        "Pemeriksaan kedekatan data sintetis CTGAN terhadap data asli.",
    ),
}


def asset_path(filename: str) -> str:
    return os.path.join(ASSETS_DIR, filename)


def available() -> list[str]:
    """Nama file gambar yang benar-benar ada di folder assets/."""
    if not os.path.isdir(ASSETS_DIR):
        return []
    return sorted(f for f in FIGURES if os.path.exists(asset_path(f)))


def missing() -> list[str]:
    return sorted(set(FIGURES) - set(available()))
