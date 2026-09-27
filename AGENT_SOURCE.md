# Aplikasi web prediksi risiko mahasiswa (EBM + CTGAN)

Implementasi web berbasis **Streamlit** dari model *Explainable Boosting
Machine* (EBM) dengan pendekatan **CTGAN** untuk klasifikasi risiko
ketidaklulusan mahasiswa (dataset OULAD), sesuai dengan penelitian skripsi.

Aplikasi ini **tidak melatih ulang model**. Ia memuat artefak yang sudah
dihasilkan di notebook riset, sehingga hasil prediksi di web konsisten dengan
hasil evaluasi pada Bab 4.

## Struktur folder

```
student-classification/
├── app.py                        # Entry point: page config + st.navigation (navbar hidden)
├── .streamlit/
│   └── config.toml               # Tema dan opsi browser
├── app_pages/                    # Halaman (WAJIB app_pages, bukan pages/)
│   ├── predict.py                # Prediksi individual
│   └── about.py                  # Tentang model: ringkasan dan batasan
├── src/
│   ├── config.py                 # Konstanta, urutan fitur, metrik
│   ├── form_config.py            # Default, bounds, label, help, preset
│   ├── preprocessing.py          # Feature engineering
│   ├── prediction.py             # Model inference
│   ├── explanation.py            # EBM local explanation
│   ├── assets.py                 # Registry gambar
│   ├── validation.py             # Validasi input
│   └── batch.py                  # Utilitas CSV non-UI (tidak dipakai halaman)
├── assets/                       # 12 gambar dari notebook
├── models/                       # Artefak model
├── scripts/
│   └── generate_feature_ranges.py
├── tests/
├── requirements.txt
└── README.md
```

> Halaman memakai `app_pages/`, bukan `pages/`. Folder `pages/` milik Streamlit
> dan tidak boleh dipakai bersama `st.navigation`.

> Navbar disembunyikan lewat `st.navigation(PAGES, position="hidden")`. Karena
> tidak ada navbar, `app.py` wajib menautkan halaman yang sedang tidak aktif
> (`st.page_link`), dan setiap halaman wajib punya `st.title` sendiri. Jangan
> pernah memakai `st.sidebar` — sidebar harus tetap kosong.

## Cara menjalankan

```bash
pip install -r requirements.txt
streamlit run app.py
```

Aplikasi terbuka di `http://localhost:8501`.

## Artefak model

Letakkan file berikut di folder `models/`:

| File | Isi |
|---|---|
| `04_final_model.pkl` | Model EBM terlatih |
| `03_scaler.pkl` | `StandardScaler` untuk 34 fitur numerik |
| `label_encoders.pkl` | Label encoder fitur kategorikal |
| `module_stats.json` | Pass rate per modul dan presentasi |
| `feature_ranges.json` | Rentang nilai fitur dari data latih |

Tiga file pertama wajib ada agar prediksi berjalan. Tanpa `module_stats.json`,
fitur kesulitan modul dan presentasi memakai nilai default global, sehingga
prediksi tetap jalan tetapi kurang akurat. Tanpa `feature_ranges.json`, validasi
rentang dilewati.

`module_stats.json` dihasilkan dari notebook:

```python
import json

module_stats = {
    "module_pass_rate": module_pass_rate_train.to_dict(),
    "presentation_pass_rate": {
        f"{m}_{p}": v for (m, p), v in pres_pass_rate_train.items()
    },
    "global_pass_rate": float(global_pass_rate_train),
}
with open("module_stats.json", "w", encoding="utf-8") as f:
    json.dump(module_stats, f, indent=2)
```

> Sesuaikan nama variabel di atas dengan nama aktual pada notebook.

### Export tambahan (opsional)

`results_summary.json` tidak dipakai aplikasi. Halaman dashboard sudah dihapus,
jadi metrik di `src/config.py` (`MODEL_METRICS`) kini hanya serves sebagai
referensi hasil evaluasi di notebook.

## Fitur aplikasi

Hanya ada dua halaman, tanpa navbar dan tanpa sidebar:

- **Prediksi individual** — form 32 field (demografi, riwayat studi, hasil
  assessment, aktivitas VLE) plus tombol preset dan *local explanation* EBM
  yang menunjukkan kontribusi tiap fitur terhadap prediksi. Dropdown modul dan
  presentasi saling bergantung: hanya kombinasi yang benar-benar ada di OULAD
  yang bisa dipilih. Tiga skor kesulitan ditampilkan sebagai metric read-only.
- **Tentang model** — cara kerja model, struktur input, batasan penggunaan, dan
  daftar artefak model.

Halaman prediksi batch dan dashboard model sudah dihapus atas permintaan
pengguna. Logikanya (`src/batch.py`, `predict_students()`,
`get_global_importance()`) masih ada sebagai utilitas non-UI dan masih teruji,
tetapi tidak dirender di mana pun.

## Konvensi penting

- **Urutan fitur tidak boleh diubah.** `FEATURE_ORDER` di `src/config.py` harus
  identik dengan `model.feature_names_in_` (40 fitur).
- **`code_module` dan `code_presentation` harus berpasangan.** OULAD hanya
  membuka 22 dari 28 kombinasi (misalnya modul `AAA` hanya punya `2013J` dan
  `2014J`). Kombinasi yang tidak pernah ada membuat `skor_kesulitan_presentasi`
  jatuh ke fallback global dan jadi tidak informatif, jadi pasangan seperti ini
  **ditolak**, bukan diterima diam-diam. Pasangan yang valid diturunkan dari
  kunci `presentation_pass_rate` di `module_stats.json` lewat
  `presentation_pairs()` — jangan pakai `CODE_MODULES × CODE_PRESENTATIONS`.
- **Skor kesulitan tidak boleh diisi manual.** `skor_kesulitan_modul`,
  `skor_kesulitan_presentasi`, dan `skor_disesuaikan_kesulitan` dihitung dari
  `module_stats.json`. Mengizinkan input manual akan membuat prediksi melenceng
  dari hasil evaluasi Bab 4.
- **Field modul/presentasi dirender di luar `st.form`.** Widget di dalam form
  tidak memicu rerun, sehingga opsi presentasi tidak bisa ikut berubah saat
  modul diganti. Field-nya ada di `MODULE_FIELDS`, terpisah dari
  `FORM_SECTIONS`.
- **Definisi field form tinggal di `src/form_config.py`.** Label, batas
  min/max, help text, dan preset didefinisikan satu kali di sana, lalu dipakai
  oleh halaman prediksi, halaman tentang model, dan test.
- **Nilai preset harus valid terhadap `feature_ranges.json` dan pasangan modul
  presentasi yang nyata.** Ada test yang menjaga kedua invariant ini.
- **Tampilan diatur lewat `.streamlit/config.toml`, bukan CSS yang di-inject.**
  Jangan gunakan `st.markdown(unsafe_allow_html=True)` untuk styling.
- **Grafik memakai komponen chart bawaan Streamlit** (`st.bar_chart`, `st.image`),
  bukan Plotly atau Matplotlib. Kalau butuh grafik kustom, pakai Vega-Lite
  lewat `st.altair_chart`.
- **Nama icon Material harus benar.** `tests/test_app.py` memvalidasi semua
  `:material/...:` di `app.py` dan `app_pages/`; nama yang tidak ada membuat
  halaman crash saat render.
- **Kalimat dan label UI memakai sentence case**, bukan Title Case.
- **Logika bisnis harus tetap bisa diuji tanpa browser.** Modul di `src/`
  tidak boleh memanggil `st.*` secara langsung, kecuali `src/prediction.py`
  yang memakai `@st.cache_resource` untuk memuat artefak. `src/batch.py`,
  `src/validation.py`, dan `src/form_config.py` tetap murni fungsi biasa.

## Testing

```bash
python -m pytest -q
```

Test memakai `streamlit.testing.v1.AppTest` untuk memeriksa render setiap
halaman dan perilaku tombol preset.

Batasan `AppTest` yang diketahui:

- Tidak bisa memicu `st.form_submit_button`. Jalur submit diuji dengan menyalin
  `predict.py` ke file sementara lalu mengganti penjaga
  `if not submitted: st.stop()` menjadi `submitted = True` (`_submitted_page()`
  di `tests/test_app.py`).
- Tidak mengemulasikan routing `?page=` milik `st.navigation`; selalu
  menghasilkan halaman default. Jadi perpindahan halaman di `app.py` tidak bisa
  diuji lewat `AppTest` — cukup dijaga lewat test yang memeriksa source.

Karena navbar disembunyikan, yang paling sering rusak adalah `app.py` dan judul
halaman. Test yang wajib tetap hijau: `test_navbar_is_hidden_and_sidebar_stays_empty`,
`test_every_page_has_its_own_title`, `test_all_material_icons_are_valid`, dan
seluruh test berawalan `test_submit_path`.

## Deployment

Aplikasi bisa di-deploy ke **Streamlit Community Cloud**:

1. Unggah folder ini beserta isi `models/` ke repository GitHub.
2. Hubungkan repository di [share.streamlit.io](https://share.streamlit.io) dan
   tunjuk `app.py` sebagai entry point.
3. Pastikan `requirements.txt` ikut ter-commit.

> Periksa batas ukuran repository: file model EBM berukuran kecil, tetapi
> `assets/` menambah beberapa MB.
