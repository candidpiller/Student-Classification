"""
Arah pengaruh tiap field terhadap risiko, diukur dari model EBM terpasang.

Angka di ``FIELD_EFFECT`` BUKAN asumsi domain. Metodenya: satu field dinaikkan
dari batas bawah ke batas atas dalam 21 titik sama jarak sambil field lain
ditahan pada profil ``CONTOH_TIDAK_BERISIKO``, lalu perubahan probabilitas
risiko diamati.

Arah ditentukan dari SELURUH kurva risiko (``src.prediction.classify_direction``),
bukan dari dua ujungnya saja. Versi lama hanya membandingkan nilai pertama dan
terakhir, sehingga kurva yang naik-turun di tengah tetap diklaim sebagai
"Naik = lebih berisiko" atau "Naik = lebih aman".

Kategori arah:

    naik_aman              nilai lebih tinggi = risiko lebih rendah
    naik_berisiko          nilai lebih tinggi = risiko lebih tinggi
    risiko_puncak_tengah   risiko tertinggi di tengah rentang
    tidak_monoton          responsnya naik-turun, tidak ada aturan monoton
    netral                 efek di bawah AMBANG_EFFECT, terlalu kecil untuk
                           disebut baik/buruk

``dampak`` adalah RENTANG probabilitas risiko, yaitu risiko tertinggi dikurangi
terendah sepanjang rentang nilai field. Dipakai range, bukan selisih kedua
ujung, karena field non-monoton bisa punya selisih ujung kecil padahal
risikonya bergerak jauh di tengah rentang.

``penting`` adalah persentase term importance EBM, dibagi rata ke tiap fitur
yang muncul pada term (term bisa berupa interaksi dua fitur).

PENTING: hubungan ini tidak kausal dan tidak independen. Mengubah satu field
ikut menggeser fitur turunan hasil ``hitung_fitur_turunan``, jadi efek antar
field saling tumpang tindih. Arah diukur sebagai efek MARGINAL: satu field
diubah, field lain ditahan. Karena itu arahnya tidak boleh dibaca dari
perbandingan dua contoh profil -- di situ ada puluhan field yang sekaligus
berbeda.

Satu-satunya hal yang BOLEH disimpulkan dari dua contoh profil: untuk field
yang berarah monoton, nilai pada "Contoh berisiko" harus berada di sisi yang
lebih berisiko dibanding "Contoh tidak berisiko". Aturan itu dijaga test
``tests/test_form_config.py``.

Untuk memperbarui angka ini setelah model dilatih ulang:

    python scripts/generate_field_effect.py --write
"""
from src.config import AMBANG_EFFECT
from src.field_spec import FIELD_BOUNDS, FIELD_HELP, field_label

# BEGIN GENERATED FIELD_EFFECT
FIELD_EFFECT: dict[str, dict] = {
    "jarak_akses_terakhir": {"arah": "tidak_monoton", "dampak": 0.836, "penting": 14.86},
    "jumlah_assessment": {"arah": "tidak_monoton", "dampak": 0.776, "penting": 10.53},
    "jumlah_mahasiswa_presentasi": {"arah": "risiko_puncak_tengah", "dampak": 0.533, "penting": 6.08},
    "rata_rata_nilai_assessment": {"arah": "risiko_puncak_tengah", "dampak": 0.744, "penting": 4.66},
    "rata_rata_sks_modul": {"arah": "risiko_puncak_tengah", "dampak": 0.251, "penting": 4.56},
    "durasi_pembelajaran_hari": {"arah": "naik_aman", "dampak": 0.716, "penting": 4.5},
    "jumlah_hari_akses": {"arah": "risiko_puncak_tengah", "dampak": 0.196, "penting": 3.58},
    "klik_tengah": {"arah": "tidak_monoton", "dampak": 0.542, "penting": 2.36},
    "min_nilai_assessment": {"arah": "risiko_puncak_tengah", "dampak": 0.173, "penting": 1.97},
    "max_nilai_assessment": {"arah": "risiko_puncak_tengah", "dampak": 0.213, "penting": 1.67},
    "std_nilai_assessment": {"arah": "risiko_puncak_tengah", "dampak": 0.203, "penting": 1.55},
    "klik_akhir": {"arah": "naik_aman", "dampak": 0.669, "penting": 1.55},
    "jumlah_assessment_banked": {"arah": "naik_berisiko", "dampak": 0.663, "penting": 1.51},
    "std_click_events": {"arah": "naik_aman", "dampak": 0.125, "penting": 1.42},
    "klik_awal": {"arah": "tidak_monoton", "dampak": 0.158, "penting": 1.4},
    "rata_rata_click_per_aktivitas": {"arah": "risiko_puncak_tengah", "dampak": 0.322, "penting": 1.34},
    "total_click_events": {"arah": "tidak_monoton", "dampak": 0.189, "penting": 1.21},
    "hari_pertama_akses": {"arah": "tidak_monoton", "dampak": 0.772, "penting": 1.13},
    "kemiringan_klik_mingguan": {"arah": "tidak_monoton", "dampak": 0.365, "penting": 1.1},
    "studied_credits": {"arah": "naik_berisiko", "dampak": 0.631, "penting": 1.05},
    "tren_klik": {"arah": "netral", "dampak": 0.05, "penting": 1.02},
    "konsistensi_keterlibatan": {"arah": "naik_berisiko", "dampak": 0.195, "penting": 0.81},
    "num_of_prev_attempts": {"arah": "tidak_monoton", "dampak": 0.193, "penting": 0.27},
}
# END GENERATED FIELD_EFFECT

DIRECTION_LABEL = {
    "naik_aman": "Naik = lebih aman",
    "naik_berisiko": "Naik = lebih berisiko",
    "risiko_puncak_tengah": "Puncak risiko di tengah rentang",
    "tidak_monoton": "Tidak monoton: risiko naik-turun",
    # Jangan menulis "tidak memengaruhi" di sini. Semua field berlabel netral
    # tetap fitur model yang dilatih memakainya; yang kecil hanya rentang
    # risikonya.
    #
    # Jangan juga menulis "tidak monoton" di sini. Field berlabel netral
    # keluaran lebih awal, sebelum monotonitas sempat diperiksa, jadi kurvanya
    # bisa saja monoton -- hanya terlalu kecil efeknya untuk disebut berarah.
    "netral": "Pengaruh kecil: arah tidak berarti, tetap dipakai model",
}

# Field dengan pengaruh kecil. Semuanya fitur model, jadi TIDAK BOLEH dihapus
# dari form -- menghapusnya membuat predict_student gagal dengan KeyError
# karena hitung_fitur_turunan dan matriks fitur masih membutuhkannya. Yang
# dilakukan hanya memindahkannya ke expander, supaya form utama tidak dipenuhi
# field yang pengaruhnya kecil.
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


def effect_gaps() -> list[str]:
    """Field numerik yang belum punya efek atau efek yang bukan field numerik."""
    problems = []
    missing = sorted(set(FIELD_BOUNDS) - set(FIELD_EFFECT))
    if missing:
        problems.append(f"field numerik tanpa FIELD_EFFECT: {missing}")

    extra = sorted(set(FIELD_EFFECT) - set(FIELD_BOUNDS))
    if extra:
        problems.append(f"FIELD_EFFECT punya field non-numerik: {extra}")

    return problems


def effect_problems() -> list[str]:
    """Konsistensi internal tabel efek: arah dikenal dan ambang netral benar."""
    problems = effect_gaps()

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

    return problems
