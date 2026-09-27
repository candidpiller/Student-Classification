"""
Modul assets — lokasi gambar statis hasil notebook beserta deskripsinya.
"""
import os

ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets"
)

# name file -> (judul, keterangan)
FIGURES = {
    "fig_confusion_matrix.png": (
        "Confusion matrix",
        "Klasifikasi silang prediksi terhadap label sebenarnya pada data uji.",
    ),
    "fig_roc_curve.png": (
        "Kurva ROC",
        "Trade-off antara true positive rate dan false positive rate (AUC 0.9764).",
    ),
    "fig_pr_curve.png": (
        "Kurva precision-recall",
        "Kinerja pada kelas minoritas Berisiko (PR-AUC 0.9668).",
    ),
    "fig_feature_importance.png": (
        "Feature importance global",
        "Kontribusi rata-rata tiap fitur terhadap keputusan model.",
    ),
    "fig_shape_functions.png": (
        "Shape function",
        "Bentuk pengaruh tiap fitur terhadap nilai log-odds.",
    ),
    "fig_local_explanation.png": (
        "Local explanation",
        "Contoh kontribusi fitur untuk satu mahasiswa.",
    ),
    "fig_metrik_train_test.png": (
        "Metrik train vs test",
        "Perbandingan metrik pada data latih dan data uji.",
    ),
    "fig_distribusi_target.png": (
        "Distribusi target",
        "Sebaran kelas target sebelum proses balancing.",
    ),
    "fig_imbalance_sebelum.png": (
        "Imbalance sebelum CTGAN",
        "Kondisi data latih sebelum oversampling CTGAN.",
    ),
    "fig_imbalance_setelah_ctgan.png": (
        "Imbalance setelah CTGAN",
        "Kondisi data latih setelah oversampling CTGAN.",
    ),
    "fig_imbalance_comparison.png": (
        "Perbandingan sebelum dan sesudah",
        "Perbandingan distribusi kelas sebelum dan sesudah CTGAN.",
    ),
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
