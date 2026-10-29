"""
Spesifikasi field form — default, batas, label, help, dan susunan section.

Modul ini sengaja hanya berisi data statis tentang field. Perhitungan efek
field ada di ``src.field_effect`` dan contoh profil ada di ``src.presets``.
Dengan pemisahan ini, halaman form tidak perlu memuat data efek hanya untuk
merender widget.
"""
from src.config import CODE_MODULES, CODE_PRESENTATIONS, DEFAULT_CATEGORIES

# Field yang bergantung satu sama lain dan karena itu dirender DI LUAR st.form.
# Widget di dalam form tidak memicu rerun, sehingga opsi presentasi tidak bisa
# ikut berubah saat modul diganti. Dipindah ke luar form supaya opsinya bisa
# difilter per modul secara langsung.
MODULE_FIELDS = ["code_module", "code_presentation"]

# Field yang diisi user, dipisah per bagian form.
# MODULE_FIELDS sengaja tidak ada di sini karena dirender terpisah di atas form.
FORM_SECTIONS = [
    ("1. Profil mahasiswa", [
        "gender", "region", "highest_education", "imd_band", "age_band",
        "disability",
    ]),
    ("2. Riwayat akademik", [
        "num_of_prev_attempts", "studied_credits",
        "rata_rata_sks_modul", "jumlah_mahasiswa_presentasi",
    ]),
    ("3. Assessment", [
        "jumlah_assessment", "rata_rata_nilai_assessment",
        "std_nilai_assessment", "min_nilai_assessment", "max_nilai_assessment",
        "jumlah_assessment_banked",
    ]),
    ("4. Aktivitas pembelajaran (VLE)", [
        "total_click_events", "rata_rata_click_per_aktivitas", "std_click_events",
        "hari_pertama_akses", "jumlah_hari_akses",
        "durasi_pembelajaran_hari", "klik_awal", "klik_tengah", "klik_akhir",
    ]),
    ("5. Aktivitas temporal", [
        "tren_klik", "jarak_akses_terakhir", "konsistensi_keterlibatan",
        "kemiringan_klik_mingguan",
    ]),
]


def widget_key(field: str) -> str:
    """Kunci session state tiap widget: ``f_`` + nama field."""
    return f"f_{field}"


# One source of truth untuk nilai default form.
FORM_DEFAULTS = {
    # 1. Profil Mahasiswa
    "gender": "M",
    "region": "East Anglian Region",
    "highest_education": "No Formal quals",
    "imd_band": "0-10%",
    "age_band": "0-35",
    "disability": "N",
    # 2. Riwayat Akademik
    "num_of_prev_attempts": 0,
    "studied_credits": 60,
    "code_module": "AAA",
    "code_presentation": "2013J",
    "rata_rata_sks_modul": 60,
    "jumlah_mahasiswa_presentasi": 500,
    # 3. Assessment
    "jumlah_assessment": 8.0,
    "rata_rata_nilai_assessment": 75.0,
    "std_nilai_assessment": 8.0,
    "min_nilai_assessment": 50.0,
    "max_nilai_assessment": 90.0,
    "jumlah_assessment_banked": 0.0,
    # 4. Aktivitas Pembelajaran (VLE)
    "total_click_events": 1500.0,
    "rata_rata_click_per_aktivitas": 5.0,
    "std_click_events": 10.0,
    "hari_pertama_akses": 0.0,
    "jumlah_hari_akses": 90.0,
    "durasi_pembelajaran_hari": 200.0,
    "klik_awal": 500.0,
    "klik_tengah": 500.0,
    "klik_akhir": 500.0,
    # 5. Aktivitas Temporal
    "tren_klik": 1.0,
    "jarak_akses_terakhir": 20.0,
    "konsistensi_keterlibatan": 0.3,
    "kemiringan_klik_mingguan": 0.0,
}

# Label yang tampil di form (sentence case).
FIELD_LABELS = {
    "gender": "Jenis kelamin",
    "region": "Wilayah",
    "highest_education": "Pendidikan tertinggi",
    "imd_band": "IMD band",
    "age_band": "Kelompok usia",
    "disability": "Disabilitas",
    "num_of_prev_attempts": "Jumlah percobaan sebelumnya",
    "studied_credits": "Studied credits (SKS)",
    "code_module": "Kode modul",
    "code_presentation": "Kode presentasi",
    "rata_rata_sks_modul": "Rata-rata SKS modul",
    "jumlah_mahasiswa_presentasi": "Jumlah mahasiswa presentasi",
    "jumlah_assessment": "Jumlah assessment",
    "rata_rata_nilai_assessment": "Rata-rata nilai assessment",
    "std_nilai_assessment": "Standar deviasi nilai",
    "min_nilai_assessment": "Nilai assessment minimum",
    "max_nilai_assessment": "Nilai assessment maksimum",
    "jumlah_assessment_banked": "Jumlah assessment banked",
    "total_click_events": "Total click events",
    "rata_rata_click_per_aktivitas": "Rata-rata click per aktivitas",
    "std_click_events": "Standar deviasi click",
    "hari_pertama_akses": "Hari pertama akses",
    "jumlah_hari_akses": "Jumlah hari akses",
    "durasi_pembelajaran_hari": "Durasi pembelajaran (hari)",
    "klik_awal": "Klik periode awal",
    "klik_tengah": "Klik periode tengah",
    "klik_akhir": "Klik periode akhir",
    "tren_klik": "Tren klik",
    "jarak_akses_terakhir": "Hari akses terakhir (relatif)",
    "konsistensi_keterlibatan": "Konsistensi keterlibatan",
    "kemiringan_klik_mingguan": "Kemiringan klik mingguan",
}

# Batas (min, max, step) tiap input numerik.
FIELD_BOUNDS = {
    "num_of_prev_attempts": (0, 6, 1),
    "studied_credits": (30, 655, 10),
    "rata_rata_sks_modul": (35, 91, 1),
    "jumlah_mahasiswa_presentasi": (300, 2500, 10),
    "jumlah_assessment": (0.0, 28.0, 1.0),
    "rata_rata_nilai_assessment": (0.0, 100.0, 0.5),
    "std_nilai_assessment": (0.0, 70.0, 0.5),
    "min_nilai_assessment": (0.0, 100.0, 1.0),
    "max_nilai_assessment": (0.0, 100.0, 1.0),
    "jumlah_assessment_banked": (0.0, 12.0, 1.0),
    "total_click_events": (0.0, 28615.0, 10.0),
    "rata_rata_click_per_aktivitas": (0.0, 20.0, 0.5),
    "std_click_events": (0.0, 310.0, 0.5),
    "hari_pertama_akses": (-25.0, 234.0, 1.0),
    "jumlah_hari_akses": (0.0, 286.0, 1.0),
    "durasi_pembelajaran_hari": (0.0, 294.0, 1.0),
    "klik_awal": (0.0, 12736.0, 10.0),
    "klik_tengah": (0.0, 11020.0, 10.0),
    "klik_akhir": (0.0, 12650.0, 10.0),
    "tren_klik": (0.0, 209.0, 0.1),
    "jarak_akses_terakhir": (-25.0, 269.0, 1.0),
    "konsistensi_keterlibatan": (0.0, 1.0, 0.01),
    "kemiringan_klik_mingguan": (-141.0, 138.0, 0.5),
}

FIELD_HELP = {
    "gender": "Kode gender mahasiswa pada data OULAD.",
    "region": "Wilayah lokasi mahasiswa.",
    "highest_education": "Kualifikasi pendidikan tertinggi sebelumnya.",
    "imd_band": "Peringkat deprivation index lokasi, dari 0-10% sampai 90-100%.",
    "age_band": "Kelompok usia mahasiswa.",
    "disability": "Apakah mahasiswa tercatat memiliki disabilitas.",
    "code_module": "Kode modul yang diambil. Menentukan skor kesulitan modul.",
    "code_presentation": "Kode presentasi modul. Menentukan skor kesulitan presentasi.",
    "num_of_prev_attempts": "Jumlah percobaan mahasiswa pada modul sebelumnya.",
    "studied_credits": "Total SKS yang diambil mahasiswa.",
    "rata_rata_sks_modul": "Rata-rata SKS pada modul yang diambil.",
    "jumlah_mahasiswa_presentasi": "Jumlah mahasiswa pada kombinasi modul dan presentasi ini.",
    "jumlah_assessment": "Jumlah assessment yang dikerjakan mahasiswa.",
    "min_nilai_assessment": "Nilai assessment terendah.",
    "rata_rata_nilai_assessment": "Rata-rata nilai seluruh assessment.",
    "max_nilai_assessment": "Nilai assessment tertinggi.",
    "std_nilai_assessment": "Variabilitas nilai assessment.",
    "jumlah_assessment_banked": "Jumlah assessment yang memakai nilai banked.",
    "total_click_events": "Jumlah seluruh aktivitas klik mahasiswa pada VLE.",
    "hari_pertama_akses": "Hari pertama mahasiswa mengakses VLE (relatif).",
    "klik_awal": "Total klik pada sepertiga awal periode aktivitas.",
    "rata_rata_click_per_aktivitas": "Rata-rata jumlah klik per aktivitas VLE.",
    "klik_tengah": "Total klik pada sepertiga tengah periode aktivitas.",
    "std_click_events": "Variabilitas jumlah klik harian.",
    "jumlah_hari_akses": "Jumlah hari berbeda mahasiswa mengakses VLE.",
    "klik_akhir": "Total klik pada sepertiga akhir periode aktivitas.",
    "durasi_pembelajaran_hari": "Durasi antara akses pertama dan akses terakhir.",
    "jarak_akses_terakhir": (
        "Hari relatif akses terakhir ke VLE, dihitung dari mulai modul. "
        "Nilai negatif berarti mahasiswa berhenti sebelum modul dimulai; nilai "
        "tinggi berarti ia masih aktif sampai modul mendekati selesai. "
        "Fitur paling berpengaruh pada model."
    ),
    "konsistensi_keterlibatan": "Ukuran konsistensi aktivitas harian mahasiswa.",
    "tren_klik": "Rasio aktivitas akhir terhadap aktivitas awal.",
    "kemiringan_klik_mingguan": "Arah dan perubahan aktivitas dari minggu ke minggu.",
}

# Opsi selectbox per field kategorikal.
SELECT_OPTIONS = {
    "gender": DEFAULT_CATEGORIES["gender"],
    "region": DEFAULT_CATEGORIES["region"],
    "highest_education": DEFAULT_CATEGORIES["highest_education"],
    "imd_band": DEFAULT_CATEGORIES["imd_band"],
    "age_band": DEFAULT_CATEGORIES["age_band"],
    "disability": DEFAULT_CATEGORIES["disability"],
    "code_module": CODE_MODULES,
    "code_presentation": CODE_PRESENTATIONS,
}

NUMERIC_FORM_FIELDS = [f for f in FORM_DEFAULTS if f not in SELECT_OPTIONS]

# Field yang dikumpulkan di form tapi tidak jadi fitur model. Dahulu berisi
# `hari_terakhir_akses`, yang sudah dihapus dari form karena sweep nilai
# membuktikan perubahannya tidak memengaruhi risiko sama sekali.
NON_MODEL_FORM_FIELDS: list[str] = []


def field_label(field: str) -> str:
    """Label form, dilengkapi rentang untuk input numerik."""
    base = FIELD_LABELS.get(field, field)
    bounds = FIELD_BOUNDS.get(field)
    if bounds is None:
        return base
    lo, hi = bounds[0], bounds[1]

    def _fmt(value):
        return f"{value:g}"

    return f"{base} ({_fmt(lo)}\u2013{_fmt(hi)})"
