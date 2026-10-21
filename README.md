# Student Risk Prediction

Prediksi risiko ketidaklulusan mahasiswa berbasis **Explainable Boosting Machine (EBM)** dengan **CTGAN** untuk data balancing.

Aplikasi ini berjalan sebagai Streamlit multipage dengan dua halaman: prediksi
individual dan tentang model. Navbar disembunyikan, jadi aplikasi tampil sebagai
satu halaman penuh tanpa sidebar; perpindahan halaman memakai tautan di bagian atas.

## Tech stack

- Python 3.11+ (teruji pada 3.11.9 dan 3.14.7)
- Streamlit (teruji pada 1.63.0)
- Pandas, NumPy
- Scikit-learn 1.7.2 — di-pin, lihat [Batasan Python](#batasan-python-scikit-learn-menentukan-versi)
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

### Regenerasi tabel arah nilai

Tabel arah nilai di `src/form_config.py` (`FIELD_EFFECT`) diukur dari model EBM
yang terpasang. Untuk memperbaruinya — misalnya setelah model dilatih ulang:

```bash
python scripts/generate_field_effect.py
```

Script menyapu tiap field sepanjang rentangnya (21 titik) pada profil
`CONTOH_TIDAK_BERISIKO`, mencetak blok `FIELD_EFFECT` yang baru untuk
disalin ke `src/form_config.py`, dan sekaligus memeriksa apakah panduan itu
masih sejalan dengan dua contoh profil di aplikasi.

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

### Batasan Python: `scikit-learn` menentukan versi

Community Cloud memakai **uv**, bukan pip, untuk instalasi. Cloud yang pernah
menjalankan app ini memakai **Python 3.14.7**, dan `scikit-learn==1.6.1` hanya
punya wheel cp310–cp313. Akibatnya sklearn harus di build dari source dan
instalasi memakan **46 menit**:

```
[16:39:51] Processing dependencies...
          Using Python 3.14.7 environment at /home/adminuser/venv
          Resolved 56 packages in 486ms
[17:26:23] Python dependencies were installed      ← 46 menit 32 detik
```

`requirements.txt` kini pin `scikit-learn==1.7.2` — versi pertama yang punya
wheel cp314 — sehingga instalasi cepat di Python mana pun yang dipilih Cloud.
Naik ke 1.7.2 sudah divalidasi: 146 test lulus dan probabilitas prediksi identik
bit-per-bit dengan 1.6.1.

Dua hal yang perlu diketahui:

- `03_scaler.pkl` dan `label_encoders.pkl` masih diserialisasi saat sklearn
  1.6.1, jadi memuatnya di 1.7.2 memunculkan dua `InconsistentVersionWarning`.
  Itu warning, bukan error, dan hasilnya sudah terbukti sama. Kalau warning
  ini tidak diinginkan, ekspor ulang kedua artefak itu memakai 1.7.2.
- `scikit-learn` di-pin dengan sengaja. Menurunkannya ke versi yang tidak punya
  wheel untuk Python yang sedang dipakai akan mengembalikan build 46 menit.

Memilih versi Python tetap hanya bisa lewat dropdown **"Python version"** di
**Advanced settings** saat deploy — `runtime.txt` dan `.python-version` sama
sekali tidak dibaca Community Cloud. Mengubahnya pada app yang sudah
ter-deploy harus lewat **hapus app lalu deploy ulang**.

Dua batasan lain dari Community Cloud: protobuf yang kompatibel adalah
`>=3.20,<6`, dan `streamlit` sebaiknya di-pin agar tidak di-upgrade diam-diam.

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
│   ├── generate_feature_ranges.py
│   └── generate_field_effect.py
└── tests/
```

> `src/batch.py`, `predict_students()`, dan `get_global_importance()` masih ada di
> repo sebagai utilitas non-UI (masih teruji), tetapi tidak lagi dipakai halaman
> mana pun setelah halaman batch dan dashboard dihapus.

## Halaman aplikasi

| Halaman | Isi |
|---------|-----|
| Prediksi individual | Form 31 field, tombol preset, panduan arah nilai, skor kesulitan otomatis, local explanation EBM |
| Tentang model | Cara kerja model, struktur input, batasan penggunaan, daftar artefak |

## Arah nilai tiap field

Tidak semua field mengikuti aturan "nilai tinggi = lebih baik". Arah pengaruh tiap
field diukur **langsung dari model EBM**, bukan dari asumsi umum, lalu hasilnya
ditampilkan di aplikasi: di tooltip setiap input dan di tabel referensi di dalam
expander "Panduan arah nilai setiap field".

### Cara mengukur

Satu field dinaikkan sepanjang rentangnya dalam **21 titik** sama jarak,
sementara field lain ditahan pada profil `CONTOH_TIDAK_BERISIKO` (risiko
0,1386, jadi tidak jenuh di batas). Angka yang disimpan adalah **rentang**
probabilitas risiko, yaitu tertinggi dikurangi terendah — bukan selisih kedua
ujung, karena field non-monoton punya selisih ujung kecil padahal risikonya
bergerak jauh di tengah rentang.

Arahnya ditentukan dari **seluruh kurva** (`src/prediction.py` →
`classify_direction`), bukan dari dua ujungnya saja. Ini penting: versi lama
hanya membandingkan nilai pertama dan terakhir, sehingga kurva EBM yang
naik-turun di tengah tetap diklaim sebagai "Naik = lebih berisiko" atau "Naik =
lebih aman". Contoh konkretnya `jumlah_assessment`: pada profil yang sama, nilai
2 lebih berisiko daripada nilai 12 — persis bertentangan dengan contoh profil
yang ada di aplikasi. Field itu sekarang berlabel "tidak monoton", karena memang
tidak ada aturan monoton padanya.

Lima kategori yang muncul:

| Arah | Arti |
|------|------|
| Naik = lebih aman | Nilai lebih tinggi menurunkan risiko |
| Naik = lebih berisiko | Nilai lebih tinggi menaikkan risiko |
| Puncak risiko di tengah rentang | Non-monoton, risiko tertinggi ada di tengah |
| Tidak monoton: risiko naik-turun | Non-monoton tanpa puncak yang mencolok, tidak ada aturan arah |
| Pengaruh kecil: arah tidak berarti, tetap dipakai model | Di bawah ambang 0,10 |

Hanya empat field yang benar-benar punya arah monoton — `jarak_akses_terakhir`,
`tren_klik`, dan `kemiringan_klik_mingguan` (naik = lebih aman) serta
`jumlah_assessment_banked` (naik = lebih berisiko). Sisanya memang tidak
monoton; itu sifat kurva EBM, bukan kesalahan pengukuran.

Tiga hal yang mungkin counterintuitive dan perlu diperhatikan:

- **`jarak_akses_terakhir`** (paling berpengaruh, 17%) lebih tinggi justru lebih
  aman. Nilainya adalah *hari relatif akses terakhir*, bukan "berapa lama sudah
  tidak diakses": negatif berarti mahasiswa berhenti sebelum modul dimulai,
  tinggi berarti masih aktif sampai modul mendekati selesai. Karena itu labelnya
  diubah menjadi "Hari akses terakhir (relatif)".
- **`jumlah_assessment`** (12%) **tidak punya arah**: risikonya naik-turun
  sepanjang rentang, jadi tidak boleh diklaim "naik = lebih berisiko".
- **`total_click_events`** juga tidak monoton, meski secara intuisi "makin
  aktif makin baik".

### Panduan dan contoh profil harus sejalan

Karena efek diukur secara marginal (satu field diubah, field lain ditahan),
arah pada tabel **tidak boleh dibaca dari perbandingan dua contoh profil**:
`Contoh berisiko` dan `Contoh tidak berisiko` berbeda di puluhan field
sekaligus. Yang boleh disimpulkan cuma satu: untuk field yang berarah monoton,
nilai pada `Contoh berisiko` harus berada di sisi yang lebih berisiko dibanding
`Contoh tidak berisiko`.

Aturan itu dijaga test di `tests/test_form_config.py`, dan
`scripts/generate_field_effect.py` ikut memverifikasinya setiap kali tabel
diregenerasi. Itulah sebabnya `jumlah_assessment_banked` bernilai 2 pada contoh
berisiko: hasil ukur model menunjukkan makin banyak assessment yang memakai
nilai banked, makin tinggi risikonya.

Angka-angka ini disimpan di `FIELD_EFFECT` (`src/form_config.py`) supaya tidak
perlu memanggil model berulang kali hanya untuk menyusun tabel. Test
`tests/test_field_effect.py` mengukur ulang field paling berpengaruh dan
membandingkannya dengan angka tersimpan, sehingga data basi tertangkap saat
test — bukan saat pengguna tertipu. Fungsi pengukurannya `measure_field_effect`
(`src/prediction.py`) dipakai bersama oleh pengumpulan data dan test agar
definisinya tidak menyimpang.

### Field berlabel "pengaruh kecil" tidak bisa dihapus

Dua field masuk kategori tersebut: `std_click_events` dan
`konsistensi_keterlibatan`. Semuanya **fitur langsung model** — mengacaukan
`predict_student` dengan `KeyError`, dan mempatoknya ke default masih menggeser
risiko. Jadi kedua field itu **dilipat ke expander "Field tambahan"**, bukan
dibuang. Nilai di dalam expander tetap bagian dari `st.form` sehingga tetap
ikut terkirim saat submit, dan `tests/test_app.py` memverifikasi bahwa
mengubahnya sungguh mengubah prediksi.

Label kategori ini pernah ditulis "Hampir tidak memengaruhi risiko" dan itu
menyesatkan: `std_click_events` yang berlabel tersebut ternyata **lebih penting**
(1,5%) daripada `tren_klik` (0,7%) yang berlabel "Naik = lebih aman". Rentang
risiko dan term importance mengukur dua hal berbeda, jadi keduanya harus
ditampilkan bersama.

`hari_terakhir_akses` pernah ikut dikumpulkan padahal sweep membuktikan
perubahannya tidak menggeser risiko sama sekali, jadi field itu dihapus dari
form.

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

AppTest bisa menekan `st.form_submit_button`, tetapi tidak bisa mengemulasikan
routing `?page=` milik `st.navigation`. Karena itu jalur submit diuji dengan
menyalin `predict.py` ke file sementara lalu mengganti penjaga
`if not submitted: st.stop()` menjadi `submitted = True` — cara ini sekaligus
menghindari model dipanggil berulang kali di setiap test.
