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
    AMBANG_EFFECT, CONTOH_TIDAK_BERISIKO, FIELD_BOUNDS, FIELD_EFFECT,
)
from src.prediction import artefak_siap, measure_field_effect

pytestmark = pytest.mark.skipif(
    not artefak_siap(), reason="artefak model tidak tersedia"
)

# Toleransi longgar: yang dijaga adalah arahnya, bukan angka presisi. Pengukuran
# ulang memakai SWEEP_POINTS yang sama seperti saat pengumpulan data, tapi tetap
# bisa menyimpang sedikit karena model tidak sepenuhnya deterministik.
TOLERANSI_DAMPAK = 0.15

# Field yang paling berpengaruh dan paling mungkin berbalik arah saat retrain.
FIELD_PANJANG = [
    "jarak_akses_terakhir",
    "jumlah_assessment_banked",
    "jumlah_assessment",
    "studied_credits",
    "jumlah_mahasiswa_presentasi",
]


def _ukur(field: str) -> dict:
    low, high, _ = FIELD_BOUNDS[field]
    return measure_field_effect(field, low, high, CONTOH_TIDAK_BERISIKO)


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
