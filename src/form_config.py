"""
Konfigurasi form input — nilai default, batas input, label, dan data contoh.

Dipisahkan dari app_pages/predict.py supaya definisi field (label, batas,
default) bisa dipakai ulang dan diuji tanpa menjalankan aplikasi.
"""
from src.config import (
    CATEGORICAL_COLS, CODE_MODULES, CODE_PRESENTATIONS, DEFAULT_CATEGORIES,
    FEATURE_ORDER, REQUIRED_INPUT_FIELDS,
)

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

# Kunci session state tiap widget: "f_" + nama field.
def widget_key(field: str) -> str:
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

# ---------------------------------------------------------------------------
# Arah pengaruh tiap field terhadap risiko.
#
# Angka di bawah diukur langsung dari model EBM yang sudah dilatih, bukan
# berdasarkan asumsi domain. Metodenya: satu field dinaikkan dari batas bawah
# ke batas atas sambil field lain ditahan pada profil CONTOH_TIDAK_BERISIKO
# (risiko 0.1386, jadi tidak jenuh di batas), lalu perubahan probabilitas risiko
# diamati.
#
#   arah     : "naik_aman"      -> nilai lebih tinggi = risiko lebih rendah
#               "naik_berisiko"  -> nilai lebih tinggi = risiko lebih tinggi
#               "puncak_tengah"  -> non-monoton, terendah di tengah rentang
#               "netral"        -> efek di bawah AMBANG_EFFECT, terlalu kecil
#                                  untuk disebut baik/buruk
#   dampak   : RENTANG probabilitas risiko, yaitu risiko tertinggi dikurangi
#              terendah di sepanjang rentang nilai field (5 titik sama jarak).
#              Dipakai range, bukan selisih kedua ujung, karena field non-monoton
#              punya selisih ujung kecil padahal risikonya bergerak jauh di
#              tengah rentang. Hitung ulang lewat
#              src.prediction.measure_field_effect agar definisinya tidak
#              menyimpang dari test.
#   penting  : persentase term importance EBM, dibagi rata ke tiap fitur yang
#              muncul pada term (term bisa berupa interaksi dua fitur)
#
# PENTING: hubungan ini tidak kausal dan tidak independen. Mengubah satu field
# ikut menggeser fitur turunan hasil hitung_fitur_turunan, jadi efek antar
# field saling tumpang tindih.
#
# Untuk memperbarui angka ini, jalankan ulang sweep dengan model terbaru.
# ---------------------------------------------------------------------------
AMBANG_EFFECT = 0.10

FIELD_EFFECT: dict[str, dict] = {
    "jarak_akses_terakhir": {"arah": "naik_aman", "dampak": 0.772, "penting": 17.0},
    "jumlah_assessment": {"arah": "naik_berisiko", "dampak": 0.435, "penting": 12.3},
    "rata_rata_nilai_assessment": {"arah": "puncak_tengah", "dampak": 0.731, "penting": 5.1},
    "jumlah_mahasiswa_presentasi": {"arah": "naik_berisiko", "dampak": 0.407, "penting": 4.8},
    "rata_rata_sks_modul": {"arah": "naik_aman", "dampak": 0.146, "penting": 3.8},
    "durasi_pembelajaran_hari": {"arah": "puncak_tengah", "dampak": 0.471, "penting": 3.6},
    "jumlah_hari_akses": {"arah": "naik_aman", "dampak": 0.108, "penting": 2.8},
    "klik_tengah": {"arah": "puncak_tengah", "dampak": 0.464, "penting": 2.2},
    "klik_akhir": {"arah": "puncak_tengah", "dampak": 0.179, "penting": 2.2},
    "klik_awal": {"arah": "netral", "dampak": 0.039, "penting": 2.1},
    "max_nilai_assessment": {"arah": "naik_aman", "dampak": 0.128, "penting": 1.9},
    "min_nilai_assessment": {"arah": "naik_berisiko", "dampak": 0.102, "penting": 1.8},
    "std_click_events": {"arah": "netral", "dampak": 0.056, "penting": 1.5},
    "total_click_events": {"arah": "netral", "dampak": 0.038, "penting": 1.5},
    "hari_pertama_akses": {"arah": "puncak_tengah", "dampak": 0.344, "penting": 1.4},
    "kemiringan_klik_mingguan": {"arah": "puncak_tengah", "dampak": 0.527, "penting": 1.3},
    "jumlah_assessment_banked": {"arah": "naik_berisiko", "dampak": 0.663, "penting": 1.2},
    "rata_rata_click_per_aktivitas": {"arah": "puncak_tengah", "dampak": 0.126, "penting": 1.2},
    "studied_credits": {"arah": "naik_berisiko", "dampak": 0.458, "penting": 1.1},
    "konsistensi_keterlibatan": {"arah": "netral", "dampak": 0.075, "penting": 1.0},
    "std_nilai_assessment": {"arah": "netral", "dampak": 0.048, "penting": 0.8},
    "tren_klik": {"arah": "puncak_tengah", "dampak": 0.121, "penting": 0.7},
    "num_of_prev_attempts": {"arah": "puncak_tengah", "dampak": 0.123, "penting": 0.1},
}

DIRECTION_LABEL = {
    "naik_aman": "Naik = lebih aman",
    "naik_berisiko": "Naik = lebih berisiko",
    "puncak_tengah": "Terbaik di tengah rentang",
    # Jangan menulis "tidak memengaruhi" di sini. Semua field berlabel netral
    # tetap fitur model yang dilatih memakainya; yang kecil hanya rentang
    # risikonya, dan arahnya tidak monoton. Klaim "tidak memengaruhi" pernah
    # dipakai di sini dan terbukti menyesatkan: klik_awal berlabel netral
    # ternyata lebih penting (2,1%) dari min_nilai_assessment (1,8%) yang
    # berlabel "naik = lebih berisiko".
    "netral": "Pengaruh kecil, tidak monoton, tetap dipakai model",
}

# Field dengan pengaruh kecil dan tidak monoton. Semuanya fitur model, jadi TIDAK
# BOLEH dihapus dari form -- menghapusnya membuat predict_student gagal dengan
# KeyError karena hitung_fitur_turunan dan matriks fitur masih membutuhkannya.
# Yang dilakukan hanya memindahkannya ke expander, supaya form utama tidak
# dipenuhi field yang pengaruhnya kecil.
FIELDS_TAMBAHAN = sorted(
    (f for f, efek in FIELD_EFFECT.items() if efek["arah"] == "netral"),
    key=lambda f: -FIELD_EFFECT[f]["penting"],
)


def field_effect(field: str) -> dict | None:
    """Efek terukur sebuah field, atau None bila field tidak punya efek terukur."""
    return FIELD_EFFECT.get(field)


def field_help(field: str) -> str | None:
    """Teks help widget: deskripsi field digabung dengan arah pengaruhnya.

    Dipisah dari FIELD_HELP supaya deskripsi tetap bisa dipakai apa adanya
    (mis. di halaman about) tanpa ikut membawa anotasi arah nilai.
    """
    base = FIELD_HELP.get(field)
    efek = field_effect(field)
    if efek is None:
        return base

    arah = DIRECTION_LABEL[efek["arah"]]
    return f"{base} {arah}." if base else f"{arah}."


def effect_rows() -> list[dict]:
    """Baris tabel referensi arah nilai, diurut dari yang paling berpengaruh."""
    rows = []
    for field, efek in FIELD_EFFECT.items():
        rows.append({
            "Field": field_label(field),
            "Arah nilai": DIRECTION_LABEL[efek["arah"]],
            "Perubahan risiko": round(efek["dampak"], 3),
            "Penting (%)": round(efek["penting"], 1),
        })
    return sorted(rows, key=lambda r: -r["Penting (%)"])

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

CONTOH_BERISIKO = {
    "gender": "M", "region": "London Region", "highest_education": "Lower Than A Level",
    "imd_band": "20-30%", "age_band": "0-35", "disability": "Y",
    "num_of_prev_attempts": 2, "studied_credits": 120, "code_module": "CCC",
    "code_presentation": "2014B", "rata_rata_sks_modul": 60, "jumlah_mahasiswa_presentasi": 380,
    "jumlah_assessment": 2.0, "rata_rata_nilai_assessment": 45.0, "std_nilai_assessment": 12.0,
    "min_nilai_assessment": 20.0, "max_nilai_assessment": 65.0, "jumlah_assessment_banked": 0.0,
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
# harus lolos validasi, sedangkan form kosong memang belum boleh dipprediksi.
FORM_KOSONG: dict = {field: None for field in FORM_DEFAULTS}

PRESETS = {
    "Contoh berisiko": CONTOH_BERISIKO,
    "Contoh tidak berisiko": CONTOH_TIDAK_BERISIKO,
}


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


def validate_form_config() -> list[str]:
    """Konsistensi internal konfigurasi form. Dipakai test."""
    problems = []

    section_fields = [f for _, fields in FORM_SECTIONS for f in fields]
    if sorted(section_fields) != sorted(set(FORM_DEFAULTS) - set(MODULE_FIELDS)):
        problems.append(
            "FORM_SECTIONS + MODULE_FIELDS tidak mencakup seluruh FORM_DEFAULTS"
        )

    if len(section_fields) != len(set(section_fields)):
        problems.append("FORM_SECTIONS punya field yang dobel")

    for field in FIELD_BOUNDS:
        if field not in FORM_DEFAULTS:
            problems.append(f"FIELD_BOUNDS punya field tak dikenal: {field}")
            continue
        lo, hi, step = FIELD_BOUNDS[field]
        if lo > hi:
            problems.append(f"{field}: min lebih besar dari max")
        if step <= 0:
            problems.append(f"{field}: step harus positif")
        default = FORM_DEFAULTS[field]
        if not lo <= default <= hi:
            problems.append(f"{field}: default {default} di luar [{lo}, {hi}]")

    for field, default in FORM_DEFAULTS.items():
        if field in SELECT_OPTIONS:
            if default not in SELECT_OPTIONS[field]:
                problems.append(f"{field}: default {default!r} bukan opsi yang valid")
        elif field not in FIELD_BOUNDS:
            problems.append(f"{field}: tidak punya SELECT_OPTIONS maupun FIELD_BOUNDS")

    for name, preset in PRESETS.items():
        unknown = set(preset) - set(FORM_DEFAULTS)
        if unknown:
            problems.append(f"preset {name!r} punya field tak dikenal: {sorted(unknown)}")
        for field, value in preset.items():
            bounds = FIELD_BOUNDS.get(field)
            if bounds and not bounds[0] <= value <= bounds[1]:
                problems.append(f"preset {name!r}: {field}={value} di luar {bounds[:2]}")

    for field in CATEGORICAL_COLS:
        if field not in SELECT_OPTIONS:
            problems.append(f"kolom kategorikal tanpa selectbox: {field}")

    expected_non_model = sorted(set(FORM_DEFAULTS) - set(REQUIRED_INPUT_FIELDS))
    if expected_non_model != sorted(NON_MODEL_FORM_FIELDS):
        problems.append(
            "NON_MODEL_FORM_FIELDS tidak sinkron dengan FORM_DEFAULTS vs "
            f"REQUIRED_INPUT_FIELDS: {expected_non_model} != {sorted(NON_MODEL_FORM_FIELDS)}"
        )

    # FIELD_EFFECT harus menutup tepat semua field numerik, dan label "netral"
    # harus benar-benar dipakai hanya untuk efek di bawah ambang.
    missing_effect = sorted(set(FIELD_BOUNDS) - set(FIELD_EFFECT))
    if missing_effect:
        problems.append(f"field numerik tanpa FIELD_EFFECT: {missing_effect}")

    extra_effect = sorted(set(FIELD_EFFECT) - set(FIELD_BOUNDS))
    if extra_effect:
        problems.append(f"FIELD_EFFECT punya field non-numerik: {extra_effect}")

    for field, efek in FIELD_EFFECT.items():
        if efek["arah"] not in DIRECTION_LABEL:
            problems.append(f"{field}: arah '{efek['arah']}' tidak dikenal")
        if efek["arah"] == "netral" and efek["dampak"] >= AMBANG_EFFECT:
            problems.append(
                f"{field}: ditandai 'netral' tapi dampak {efek['dampak']} "
                f">= AMBANG_EFFECT {AMBANG_EFFECT}"
            )
        if efek["arah"] != "netral" and efek["dampak"] < AMBANG_EFFECT:
            problems.append(
                f"{field}: dampak {efek['dampak']} < AMBANG_EFFECT "
                f"{AMBANG_EFFECT}, seharusnya ditandai 'netral'"
            )

    # Field yang dilipat ke expander wajib tetap fitur model, dan tetap punya
    # default + batas. Kalau ada yang tidak, memindahkannya akan memicu KeyError.
    for field in FIELDS_TAMBAHAN:
        if field not in FEATURE_ORDER:
            problems.append(
                f"FIELDS_TAMBAHAN berisi {field} yang bukan fitur model; "
                "field seperti ini tidak boleh dilipat ke expander"
            )
        if field not in FORM_DEFAULTS:
            problems.append(f"FIELDS_TAMBAHAN berisi {field} tanpa FORM_DEFAULTS")

    if sorted(FIELDS_TAMBAHAN) != sorted(
        f for f, e in FIELD_EFFECT.items() if e["arah"] == "netral"
    ):
        problems.append("FIELDS_TAMBAHAN tidak sinkron dengan FIELD_EFFECT arah 'netral'")

    return problems