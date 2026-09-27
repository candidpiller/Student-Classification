# Student Risk Prediction

Prediksi risiko ketidaklulusan mahasiswa berbasis **Explainable Boosting Machine (EBM)** dengan **CTGAN** untuk data balancing.

Aplikasi ini berjalan sebagai Streamlit multipage dengan dua halaman: prediksi
individual dan tentang model. Navbar disembunyikan, jadi aplikasi tampil sebagai
satu halaman penuh tanpa sidebar; perpindahan halaman memakai tautan di bagian atas.

## Tech stack

- Python 3.11+
- Streamlit (teruji pada 1.63.0)
- Pandas, NumPy
- Scikit-learn
- InterpretML (EBM)
- Joblib

Semua grafik memakai komponen chart bawaan Streamlit, sehingga Plotly dan
Matplotlib tidak lagi menjadi dependensi.

## Instalasi

```bash
pip install -r requirements.txt
```

## Menyiapkan model

Artefak model harus berada di folder `models/`:

```
models/
├── 04_final_model.pkl      # Model EBM
├── 03_scaler.pkl           # StandardScaler untuk 34 fitur numerik
├── label_encoders.pkl      # Label encoders untuk fitur kategorikal
├── module_stats.json       # Statistik modul (pass rate)
└── feature_ranges.json     # Rentang nilai fitur numerik
```

Folder `assets/` berisi 12 gambar visualisasi dari notebook pelatihan. Halaman
tentang model tetap berjalan meskipun sebagian gambar tidak ada.

### Regenerasi `feature_ranges.json`

Nilai di `models/feature_ranges.json` sudah dikirim bersama proyek, jadi script
hanya perlu dijalankan bila ingin memperbarui rentang fitur:

```bash
python scripts/generate_feature_ranges.py
```

Script ini memakai `kagglehub`, yang tidak ada di `requirements.txt`. Pasang
terlebih dahulu bila memang akan menjalankannya:

```bash
pip install kagglehub
```

## Menjalankan aplikasi

```bash
streamlit run app.py
```

Tema dan setelan tampilan diatur lewat `.streamlit/config.toml` — tidak ada CSS
yang di-inject lewat `st.markdown(unsafe_allow_html=True)`.

## Deploy ke Streamlit Community Cloud

Repositori harus tetap **ringan**. Community Cloud melakukan shallow clone, jadi
hanya commit terbaru yang ditarik — tetapi commit terbaru tetap memuat seluruh
file yang ter-track. `.venv/` dan `__pycache__/` sudah masuk `.gitignore`; kalau
keduanya pernah ter-commit, `.gitignore` tidak berlaku lagi dan perlu dilepas
dari index:

```bash
git rm -r --cached .venv
git rm -r --cached --ignore-unmatch -- ':(glob)**/__pycache__/**' __pycache__
```

`models/04_final_model.pkl` (±57 MB) memang harus ikut ter-commit supaya
inference berjalan di cloud. Kalau repo jadi terlalu besar, pindahkan artefak
besar itu ke Git LFS — Community Cloud otomatis men-download LFS object saat
deploy.

### `requirements.txt` harus UTF-8

Enkoding UTF-16 menyisipkan byte `\x00` di tiap baris sehingga nama paket tidak
terbaca dan instalasi gagal. Simpan sebagai UTF-8 tanpa BOM.

### Memilih versi Python

**`runtime.txt` diabaikan oleh Streamlit Community Cloud.** File itu hanya dibaca
host yang mendukungnya (Render, Railway, Fly.io). Untuk Community Cloud, versi
Python dipilih lewat dropdown **"Python version"** di **Advanced settings** saat
deploy.

**Pilih 3.11.** Cloud pernah berjalan di Python 3.14.7, dan `scikit-learn==1.6.1`
tidak punya wheel cp314 — hanya cp311, cp312, cp313. Akibatnya sklearn harus di
build dari source dan instalasi memakan **46 menit**:

```
[16:39:51] Processing dependencies...
          Using Python 3.14.7 environment at /home/adminuser/venv
          Resolved 56 packages in 486ms
[17:26:23] Python dependencies were installed      ← 46 menit 32 detik
```

Di Python 3.11, wheel cp311 dipakai dan instalasi selesai dalam hitungan detik.
Versi ini juga sama dengan venv lokal, jadi perilaku app di cloud dan di
lokal identik.

Kalau 3.11 tidak tersedia di dropdown, naikkan `scikit-learn` ke **≥1.7.2** —
versi pertama yang punya wheel cp314. Tapi model dilatih dengan 1.6.1, jadi
artefak `.pkl` harus diuji ulang sebelumItu dianggap aman.

Dua batasan lain dari Community Cloud: protobuf yang kompatibel adalah
`>=3.20,<6`, dan `streamlit` sebaiknya di-pin agar tidak di-upgrade diam-diam.
Mengubah versi Python pada app yang sudah ter-deploy harus lewat **hapus app
lalu deploy ulang** — tidak bisa in-place.

## Struktur project

```
student-classification/
├── app.py                       # Entry point: page config + st.navigation (navbar hidden)
├── .streamlit/
│   └── config.toml              # Tema dan opsi browser
├── requirements.txt             # Dependency Python (UTF-8, tanpa BOM)
├── runtime.txt                  # Pin Python untuk host non-Community-Cloud
├── app_pages/                   # Halaman (bukan folder pages/)
│   ├── predict.py               # Form prediksi individual
│   └── about.py                 # Ringkasan model dan batasan
├── src/
│   ├── config.py                # Konstanta, feature order, metrik
│   ├── form_config.py           # Default, bounds, label, help, preset
│   ├── preprocessing.py         # Feature engineering
│   ├── prediction.py            # Model inference
│   ├── explanation.py           # EBM local explanation
│   ├── assets.py                # Registry gambar
│   └── validation.py            # Input validation
├── models/                      # Artefak model
├── assets/                      # Gambar visualisasi
├── scripts/
│   └── generate_feature_ranges.py
└── tests/
```

> `src/batch.py`, `predict_students()`, dan `get_global_importance()` masih ada di
> repo sebagai utilitas non-UI (masih teruji), tetapi tidak lagi dipakai halaman
> mana pun setelah halaman batch dan dashboard dihapus.

## Halaman aplikasi

| Halaman | Isi |
|---------|-----|
| Prediksi individual | Form 32 field, tombol preset, skor kesulitan otomatis, local explanation EBM |
| Tentang model | Cara kerja model, struktur input, batasan penggunaan, daftar artefak |

## Kesulitan modul

Tiga fitur kesulitan (`skor_kesulitan_modul`, `skor_kesulitan_presentasi`,
`skor_disesuaikan_kesulitan`) **dihitung otomatis**, bukan diisi manual, dari
`models/module_stats.json` dengan formula `1 - pass rate`.

Pasangan `code_module` + `code_presentation` saling bergantung. OULAD hanya
membuka 22 dari 28 kombinasi — modul `AAA` hanya punya `2013J` dan `2014J`,
modul `CCC` hanya `2014B` dan `2014J`. Kombinasi yang tidak pernah ada akan
ditolak, karena skor kesulitannya akan jatuh ke fallback global dan tidak lagi
informatif. Daftar pasangan yang valid diturunkan dari
`presentation_pass_rate` di `module_stats.json`.

## Target model

- **Class 0:** Berisiko (Gagal/Withdrawn)
- **Class 1:** Tidak Berisiko (Lulus/Distinction)
- **Threshold:** 0.50

## Metrik evaluasi

Metrik berikut dicatat di notebook pelatihan; halaman dashboard sudah dihapus,
jadi tabel ini tidak lagi dirender di aplikasi mana pun.

| Metrik | Nilai |
|--------|-------|
| Accuracy | 92.73% |
| AUC-ROC | 0.9764 |
| PR-AUC | 0.9668 |
| F1-Score (Macro) | 92.72% |
| Recall Kelas 0 (Gagal) | 90.41% |
| Recall Kelas 1 (Lulus) | 95.32% |

## Menjalankan test

```bash
python -m pytest -q
```

Test mencakup regresi preset form, rentang fitur, pasangan modul-presentasi,
konsistensi konfigurasi form, validitas icon Material, jalur submit (lebak patch),
dan render kedua halaman lewat `AppTest`.

AppTest tidak dapat menekan `st.form_submit_button` maupun mengemulasikan routing
`?page=` milik `st.navigation`, jadi jalur submit diuji dengan menyalin
`predict.py` ke file sementara lalu mengganti penjaga `if not submitted: st.stop()`
menjadi `submitted = True`.
