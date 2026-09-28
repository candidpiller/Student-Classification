"""Halaman tentang model — ringkasan proyek, model, dan batasan penggunaan."""
import os

import pandas as pd
import streamlit as st

from src.assets import FIGURES, asset_path
from src.config import (
    CODE_MODULES, CODE_PRESENTATIONS, DERIVED_FEATURES, FEATURES_DIFFICULTY,
    GLOBAL_PASS_RATE, MODEL_INFO, REQUIRED_INPUT_FIELDS, THRESHOLD,
)
from src.form_config import (
    CONTOH_BERISIKO, CONTOH_TIDAK_BERISIKO, FIELD_BOUNDS,
    NON_MODEL_FORM_FIELDS,
)
from src.prediction import MODELS_DIR

# Navbar disembunyikan, jadi setiap halaman punya judul sendiri.
# anchor=False menyembunyikan ikon tautan yang muncul saat hover di kanan heading.
st.title("Tentang model", anchor=False)

st.caption(
    "Aplikasi web untuk memperkirakan risiko ketidaklulusan mahasiswa memakai "
    "model Explainable Boosting Machine."
)

st.subheader("Tujuan", anchor=False)
st.markdown(
    f"""
    Aplikasi ini membantu institution memprioritaskan pendampingan bagi
    mahasiswa yang berisiko tidak lulus. Data berasal dari
    **{MODEL_INFO['dataset']}**, yaitu data virtual yang merepresentasikan
    mahasiswa Program Open University.

    Model menghasilkan dua kelas prediksi:

    - **Berisiko** — berpotensi tidak menyelesaikan studi tepat waktu.
    - **Tidak berisiko** — cenderung menyelesaikan studi tepat waktu.

    Probabilitas berisiko dihitung dengan threshold **{THRESHOLD:.2f}**.
    """
)

st.subheader("Cara kerja", anchor=False)
st.markdown(
    f"""
    1. Pengguna mengisi **{len(REQUIRED_INPUT_FIELDS)}** field input.
    2. {len(DERIVED_FEATURES)} fitur turunan dihitung otomatis dari input
       tersebut, misalnya `click_per_day` dan `nilai_x_assessment`.
    3. {len(FEATURES_DIFFICULTY)} fitur kesulitan dihitung dari
       `module_stats.json` berdasarkan kode modul dan presentasi yang dipilih.
    4. Fitur kategorikal di-encode dengan label encoder, lalu
       {len(FIELD_BOUNDS)} nilai input diskalakan dengan scaler yang tersimpan.
    5. Model EBM memprediksi probabilitas, lalu `get_local_explanation()`
       menampilkan fitur yang mendorong prediksi tersebut.
    """
)

st.subheader("Tentang model", anchor=False)
st.dataframe(
    {
        "Aspek": ["Model", "Data balancing", "Jumlah fitur", "Threshold"],
        "Nilai": [
            MODEL_INFO["name"],
            MODEL_INFO["balancing"],
            MODEL_INFO["n_features"],
            f"{THRESHOLD:.2f}",
        ],
    },
    hide_index=True,
    width="stretch",
)
st.markdown(
    f"{MODEL_INFO['balancing']} membuat sampel sintetis pada kelas minoritas "
    "agar model tidak terlalu bias ke kelas yang lebih besar."
)

st.subheader("Batasan penggunaan", anchor=False)
st.markdown(
    f"""
    - Prediksi adalah **kemungkinan statistik**, bukan keputusan final.
      Jangan dipakai sebagai satu-satunya dasar keputusan akademik.
    - Global pass rate pada dataset adalah **{GLOBAL_PASS_RATE:.1%}**. Karena
      data balancing mengubah proporsi kelas, probabilitas keluaran model tidak
      boleh dibaca sebagai prevalence absolut.
    - Fitur perilaku klik berasal dari data virtual OULAD, sehingga pola
      digital di dunia nyata bisa berbeda.
    - Aplikasi tidak menyimpan data pengguna; hanya membaca artefak model di
      folder `models/`.
    """
)

st.subheader("Struktur input", anchor=False)
baris_input = [
    f"- Field yang diisi pengguna: **{len(REQUIRED_INPUT_FIELDS)}**, termasuk "
    "`code_module` dan `code_presentation`.",
    f"- Fitur turunan: {len(DERIVED_FEATURES)}.",
    f"- Fitur kesulitan: {len(FEATURES_DIFFICULTY)}.",
    f"- Kode modul: {', '.join(CODE_MODULES)}.",
    f"- Kode presentasi: {', '.join(CODE_PRESENTATIONS)}.",
]
if NON_MODEL_FORM_FIELDS:
    non_model = ", ".join(f"`{f}`" for f in NON_MODEL_FORM_FIELDS)
    baris_input.insert(
        1,
        f"- Field form yang bukan fitur model: **{len(NON_MODEL_FORM_FIELDS)}** "
        f"({non_model}).",
    )
st.markdown("\n".join(baris_input))

with st.expander("Contoh nilai preset", icon=":material/tune:"):
    st.caption(
        "Tombol Reset form tidak memakai preset: dia mengosongkan semua kolom "
        "supaya bisa diisi dari nol."
    )
    st.dataframe(
        {
            "Field": [
                "Contoh berisiko",
                "Contoh tidak berisiko",
            ],
            "Jarak akses terakhir": [
                CONTOH_BERISIKO["jarak_akses_terakhir"],
                CONTOH_TIDAK_BERISIKO["jarak_akses_terakhir"],
            ],
        },
        hide_index=True,
        width="stretch",
    )

st.subheader("Kualitas data sintetis", anchor=False)
st.image(
    asset_path("fig_kualitas_data_sintetis.png"),
    caption=FIGURES["fig_kualitas_data_sintetis.png"][1],
    width="stretch",
)

st.subheader("Artefak model", anchor=False)
if os.path.isdir(MODELS_DIR):
    artifact_rows = [
        {
            "File": f"`models/{name}`",
            "Ukuran": f"{os.path.getsize(os.path.join(MODELS_DIR, name)) / 1024:,.1f} KB",
        }
        for name in sorted(os.listdir(MODELS_DIR))
    ]
    if artifact_rows:
        st.dataframe(pd.DataFrame(artifact_rows), hide_index=True, width="stretch")
    else:
        st.warning("Folder `models/` kosong.")
else:
    st.warning("Folder `models/` tidak ditemukan.")
