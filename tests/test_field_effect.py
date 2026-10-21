"""Test bahwa FIELD_EFFECT masih cocok dengan model yang benar-benar terpasang.

FIELD_EFFECT menyimpan angka hasil pengukuran manual terhadap model EBM. Kalau
model dilatih ulang, arah dan besaran efek bisa berubah — dan kalau begitu
petunjuk yang tampil di form jadi berbohong. Test di bawah mengukur ulang
beberapa field paling berpengaruh lalu membandingkannya dengan angka yang
disimpan, jadi data basi ketahuan saat test, bukan saat pengguna tertipu.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.form_config import (
    AMBANG_EFFECT, CONTOH_BERISIKO, CONTOH_TIDAK_BERISIKO, FIELD_BOUNDS,
    FIELD_EFFECT,
)
from src.prediction import (
    artefak_siap, classify_direction, measure_field_effect, predict_student,
)

# Toleransi longgar: yang dijaga adalah arahnya, bukan angka presisi. Pengukuran
# ulang memakai SWEEP_POINTS yang sama seperti saat pengumpulan data, tapi tetap
# bisa menyimpang sedikit karena model tidak sepenuhnya deterministik.
TOLERANSI_DAMPAK = 0.15

# Selisih risiko di bawah ini dianggap noise langkah EBM, bukan arah yang
# berbalik. Sama dengan toleransi di scripts/generate_field_effect.py.
TOLERANSI_NOISE = 0.01

# Field yang paling berpengaruh dan paling mungkin berbalik arah saat retrain.
FIELD_PANJANG = [
    "jarak_akses_terakhir",
    "jumlah_assessment_banked",
    "jumlah_assessment",
    "studied_credits",
    "jumlah_mahasiswa_presentasi",
]

# Kurva risiko `jumlah_assessment` hasil ukur di profil CONTOH_TIDAK_BERISIKO.
# Dua ujungnya naik (0,147 -> 0,582), jadi versi lama akan menyimpulkan "naik =
# lebih berisiko" -- padahal kurvanya naik-turun di tengah, dan contoh profil
# di aplikasi justru menunjukkan nilai kecil yang lebih berisiko.
KURVA_JUMLAH_ASSESSMENT = [
    0.147, 0.527, 0.221, 0.050, 0.065, 0.264, 0.278, 0.117, 0.105, 0.167,
    0.478, 0.475, 0.534, 0.522, 0.455, 0.430, 0.281, 0.480, 0.668, 0.645, 0.582,
]


def _ukur(field: str) -> dict:
    low, high, _ = FIELD_BOUNDS[field]
    return measure_field_effect(field, low, high, CONTOH_TIDAK_BERISIKO)


class TestClassifyDirection:
    """Penentuan arah dari kurva, tidak bergantung model sama sekali."""

    def test_kurva_naik_monoton_berisiko(self):
        kurva = [i / 20 for i in range(21)]

        assert classify_direction(kurva, 1.0) == "naik_berisiko"

    def test_kurva_turun_monoton_aman(self):
        kurva = [1 - i / 20 for i in range(21)]

        assert classify_direction(kurva, 1.0) == "naik_aman"

    def test_kurva_berganti_arah_tidak_diklaim_monoton(self):
        """Kurva yang berayun tidak boleh disebut monoton.

        Regression dari bug yang membuat aplikasi menulis "Naik = lebih
        berisiko" untuk `jumlah assessment`. Dua ujungnya naik, jadi cara lama
        (bandingkan ujung saja) akan salah menyimpulkan arah naik.
        """
        kurva = [0.1, 0.9, 0.1, 0.9, 0.1, 0.9, 0.1, 0.9, 0.1, 0.9]

        assert classify_direction(kurva, 0.8) == "tidak_monoton"

    def test_kurva_jumlah_assessment_terukur_tidak_monoton(self):
        rentang = max(KURVA_JUMLAH_ASSESSMENT) - min(KURVA_JUMLAH_ASSESSMENT)

        assert classify_direction(KURVA_JUMLAH_ASSESSMENT, rentang) == "tidak_monoton"

    def test_puncak_di_tengah_dilaporkan_sebagai_puncak(self):
        kurva = [0.1] * 5 + [0.9] + [0.1] * 15

        assert classify_direction(kurva, 0.8) == "risiko_puncak_tengah"

    def test_efek_kecil_dianggap_netral(self):
        kurva = [0.5 + 0.0001 * i for i in range(21)]

        assert classify_direction(kurva, 0.001) == "netral"


@pytest.mark.skipif(
    not artefak_siap(), reason="artefak model tidak tersedia"
)
class TestFieldEffectMatchesModel:
    @pytest.mark.parametrize("field", FIELD_PANJANG)
    def test_rentang_tetap_sepadan(self, field):
        terukur = _ukur(field)["rentang"]
        tersimpan = FIELD_EFFECT[field]["dampak"]

        assert abs(terukur - tersimpan) < TOLERANSI_DAMPAK, (
            f"{field}: rentang tersimpan {tersimpan} tapi hasil ukur ulang "
            f"{terukur:.3f}. Perbarui FIELD_EFFECT di src/form_config.py."
        )

    @pytest.mark.parametrize("field", FIELD_PANJANG)
    def test_arah_tetap_sepadan(self, field):
        terukur = _ukur(field)["arah"]
        tersimpan = FIELD_EFFECT[field]["arah"]

        assert terukur == tersimpan, (
            f"{field}: arah tersimpan {tersimpan!r} tapi model kini memberi "
            f"{terukur!r}. Perbarui FIELD_EFFECT di src/form_config.py."
        )

    def test_field_diabaikan_model_tidak_lagi_ada(self):
        """`hari_terakhir_akses` dihapus karena rentangnya 0.000."""
        assert "hari_terakhir_akses" not in FIELD_BOUNDS
        assert "hari_terakhir_akses" not in FIELD_EFFECT

    def test_semua_field_memakai_ambang_yang_konsisten(self):
        for field, efek in FIELD_EFFECT.items():
            if efek["arah"] == "netral":
                assert efek["dampak"] < AMBANG_EFFECT, field
            else:
                assert efek["dampak"] >= AMBANG_EFFECT, field

    def test_field_paling_berpengaruh_memang_paling_didorong_risiko(self):
        """Sanity check: span terbesar harus milik feature importance terbesar."""
        rentang = {f: _ukur(f)["rentang"] for f in FIELD_PANJANG}
        paling_besar = max(rentang, key=rentang.get)
        paling_penting = max(FIELD_PANJANG, key=lambda f: FIELD_EFFECT[f]["penting"])

        assert paling_besar == paling_penting, (
            f"rentang terbesar ada di {paling_besar}, tapi feature importance "
            f"tertinggi ada di {paling_penting}"
        )


@pytest.mark.skipif(
    not artefak_siap(), reason="artefak model tidak tersedia"
)
class TestPanduanTidakBertentanganDenganContoh:
    """Panduan arah dan dua contoh profil tidak boleh saling bertentangan.

    Ini regresi dari laporan pengguna: tabel menulis "Jumlah assessment -> naik =
    lebih berisiko", sementara contoh di aplikasi menunjukkan jumlah assessment
    kecil yang lebih berisiko. Field non-monoton kini tidak diklaim berarah,
    dan field yang berarah monoton harus punya contoh profil yang urutannya
    sesuai.
    """

    FIELD_MONOTON = [
        field for field, efek in FIELD_EFFECT.items()
        if efek["arah"] in ("naik_berisiko", "naik_aman")
    ]

    def test_ada_field_monoton_yang_diuji(self):
        """Tes harus benar-benar menguji sesuatu."""
        assert self.FIELD_MONOTON, "tidak ada field berarah monoton"

    @pytest.mark.parametrize("field", FIELD_MONOTON)
    def test_urutan_contoh_profil_sesuai_panduan(self, field):
        arah = FIELD_EFFECT[field]["arah"]
        nilai_berisiko = CONTOH_BERISIKO[field]
        nilai_aman = CONTOH_TIDAK_BERISIKO[field]

        if arah == "naik_berisiko":
            assert nilai_berisiko >= nilai_aman, (
                f"{field}: panduan bilang 'naik = lebih berisiko', tapi contoh "
                f"berisiko memakai nilai {nilai_berisiko} yang lebih rendah dari "
                f"{nilai_aman} pada contoh aman."
            )
        else:
            assert nilai_berisiko <= nilai_aman, (
                f"{field}: panduan bilang 'naik = lebih aman', tapi contoh "
                f"berisiko memakai nilai {nilai_berisiko} yang lebih tinggi dari "
                f"{nilai_aman} pada contoh aman."
            )

    @pytest.mark.parametrize("field", FIELD_MONOTON)
    def test_model_sepakat_dengan_panduan_antar_nilai_contoh(self, field):
        """Di antara kedua nilai contoh, model harus ikut arah yang diklaim."""
        arah = FIELD_EFFECT[field]["arah"]
        rendah, tinggi = sorted((CONTOH_BERISIKO[field], CONTOH_TIDAK_BERISIKO[field]))
        if rendah == tinggi:
            pytest.skip("kedua contoh memakai nilai yang sama")

        risiko = []
        for nilai in (rendah, tinggi):
            baris = dict(CONTOH_TIDAK_BERISIKO)
            baris[field] = float(nilai)
            risiko.append(predict_student(baris)["probability_risk"])

        selisih = risiko[1] - risiko[0]
        if arah == "naik_berisiko":
            assert selisih > -TOLERANSI_NOISE, (
                f"{field}: panduan bilang 'naik = lebih berisiko', tapi model "
                f"justru lebih aman pada nilai yang lebih tinggi "
                f"({risiko[0]:.3f} -> {risiko[1]:.3f})."
            )
        else:
            assert selisih < TOLERANSI_NOISE, (
                f"{field}: panduan bilang 'naik = lebih aman', tapi model "
                f"justru lebih berisiko pada nilai yang lebih tinggi "
                f"({risiko[0]:.3f} -> {risiko[1]:.3f})."
            )

    def test_field_non_monoton_tidak_diklaim_berarah(self):
        """Field yang kurvanya berayun tidak boleh punya label arah monoton."""
        for field, efek in FIELD_EFFECT.items():
            if field in self.FIELD_MONOTON:
                continue
            assert efek["arah"] not in ("naik_berisiko", "naik_aman"), (
                f"{field}: kurvanya tidak monoton tapi diklaim '{efek['arah']}'"
            )
