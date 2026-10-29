"""
Contoh profil dan nilai kosong untuk form prediksi.

Preset sengaja dipisahkan dari spesifikasi field supaya halaman form bisa
memuat ``src.field_spec`` tanpa ikut membawa data contoh yang panjang.
"""
from src.field_spec import FORM_DEFAULTS

# Dua contoh profil di bawah harus sejalan dengan panduan arah nilai:
#
#   - Untuk field yang berarah monoton ("naik_berisiko" / "naik_aman"), nilai
#     pada contoh berisiko harus berada di sisi yang lebih berisiko dibanding
#     contoh tidak berisiko.
#   - Field non-monoton tidak punya aturan arah, jadi kedua contoh boleh
#     berbeda tanpa perlu sesuai dengan suatu arah.
#
# Aturan pertama dijaga test di tests/test_form_config.py, supaya panduan dan
# contoh di aplikasi tidak pernah bertentangan.
#
# CONTOH_TIDAK_BERISIKO sekaligus jadi baseline pengukuran FIELD_EFFECT:
# risikonya cukup jauh dari batas jenuh, sehingga efek tiap field masih
# terlihat. Mengubah baseline itu berarti semua angka FIELD_EFFECT harus
# diukur ulang.
CONTOH_BERISIKO = {
    "gender": "M", "region": "London Region", "highest_education": "Lower Than A Level",
    "imd_band": "20-30%", "age_band": "0-35", "disability": "Y",
    "num_of_prev_attempts": 2, "studied_credits": 120, "code_module": "CCC",
    "code_presentation": "2014B", "rata_rata_sks_modul": 60, "jumlah_mahasiswa_presentasi": 380,
    "jumlah_assessment": 2.0, "rata_rata_nilai_assessment": 45.0, "std_nilai_assessment": 12.0,
    "min_nilai_assessment": 20.0, "max_nilai_assessment": 65.0, "jumlah_assessment_banked": 2.0,
    "total_click_events": 250.0, "rata_rata_click_per_aktivitas": 2.2, "std_click_events": 2.0,
    "hari_pertama_akses": 25.0, "jumlah_hari_akses": 15.0,
    "durasi_pembelajaran_hari": 60.0, "klik_awal": 70.0, "klik_tengah": 60.0, "klik_akhir": 30.0,
    "tren_klik": 0.42, "jarak_akses_terakhir": 85.0, "konsistensi_keterlibatan": 0.18,
    "kemiringan_klik_mingguan": -3.5,
}

CONTOH_TIDAK_BERISIKO = {
    "gender": "F", "region": "Scotland", "highest_education": "HE Qualification",
    "imd_band": "60-70%", "age_band": "35-55", "disability": "N",
    "num_of_prev_attempts": 0, "studied_credits": 60, "code_module": "AAA",
    "code_presentation": "2013J", "rata_rata_sks_modul": 60, "jumlah_mahasiswa_presentasi": 500,
    "jumlah_assessment": 12.0, "rata_rata_nilai_assessment": 90.0, "std_nilai_assessment": 7.0,
    "min_nilai_assessment": 78.0, "max_nilai_assessment": 100.0, "jumlah_assessment_banked": 1.0,
    "total_click_events": 3000.0, "rata_rata_click_per_aktivitas": 4.0, "std_click_events": 6.0,
    "hari_pertama_akses": 0.0, "jumlah_hari_akses": 130.0,
    "durasi_pembelajaran_hari": 258.0, "klik_awal": 800.0, "klik_tengah": 900.0, "klik_akhir": 1200.0,
    "tren_klik": 1.5, "jarak_akses_terakhir": 258.0, "konsistensi_keterlibatan": 0.05,
    "kemiringan_klik_mingguan": 0.5,
}

# Reset form mengosongkan semua kolom, bukan mengembalikannya ke default, supaya
# user bisa mengisi dari nol. Nilai None membuat st.number_input tampil kosong
# dan st.selectbox tanpa pilihan.
# Sengaja TIDAK dijadikan anggota PRESETS: PRESETS berisi data lengkap yang
# harus lolos validasi, sedangkan form kosong memang belum boleh diprediksi.
FORM_KOSONG: dict = {field: None for field in FORM_DEFAULTS}

PRESETS = {
    "Contoh berisiko": CONTOH_BERISIKO,
    "Contoh tidak berisiko": CONTOH_TIDAK_BERISIKO,
}
