"""Generate ulang tabel FIELD_EFFECT dari model EBM yang terpasang.

Arah pengaruh tiap field diukur dengan menyapu satu field sepanjang rentang
nilainya (21 titik) sambil field lain ditahan pada profil CONTOH_TIDAK_BERISIKO.
Arah ditentukan dari SELURUH kurva risiko, bukan dari dua ujungnya, supaya
field yang responsnya naik-turun tidak diklaim sebagai aturan monoton.

Script ini juga memeriksa apakah panduan yang dihasilkan masih sejalan dengan
dua contoh profil di aplikasi. Kalau ada pertentangan, hasilnya dicetak --
dan artinya tabel FIELD_EFFECT atau preset perlu diperbaiki.

Cara pakai:
    .venv/Scripts/python.exe scripts/generate_field_effect.py

Salin blok FIELD_EFFECT yang dicetak ke src/form_config.py.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.form_config import (
    CONTOH_BERISIKO, CONTOH_TIDAK_BERISIKO, FIELD_BOUNDS, FIELD_EFFECT,
)
from src.prediction import measure_field_effect

# Peng Importance (persentase term importance EBM) tidak dihitung di sini.
# Nilainya diambil dari model lewat get_global_importance() dan tidak berubah
# selama model tidak dilatih ulang.
PENTING_TERSIMPAN = {f: e["penting"] for f, e in FIELD_EFFECT.items()}

# Selisih risiko di bawah ini dianggap noise langkah EBM, bukan arah yang
# berbalik. Tanpa toleransi ini, kurva yang datar di satu bagian rentang akan
# selalu dianggap bertentangan dengan panduan.
TOLERANSI_NOISE = 0.01


def ukur(field: str) -> dict:
    low, high, _ = FIELD_BOUNDS[field]
    return measure_field_effect(field, low, high, CONTOH_TIDAK_BERISIKO)


def cek_konflik_preset(hasil: dict[str, dict]) -> list[str]:
    """Cari field yang arah petalsinya bertentangan dengan contoh profil.

    Dua pemeriksaan dijalankan untuk tiap field yang berarah monoton:

    1. Urutan contoh profil harus sesuai arah yang diklaim. Pada field
       "naik_berisiko", nilai contoh berisiko harus lebih tinggi daripada nilai
       contoh aman. Kalau tidak, pembaca menemukan dua hal di aplikasi ini
       yang saling bertentangan: panduan soal arahnya, contoh profil soal
       nilai yang dipakai.
    2. Model harus berpihak pada arah yang diklaim di antara kedua nilai itu.
       Pada field "naik_berisiko", nilai yang lebih tinggi harus menghasilkan
       risiko yang lebih tinggi. Selisih di bawah TOLERANSI_NOISE dianggap
       noise langkah EBM, bukan arah yang berbalik.
    """
    konflik = []
    for field, efek in hasil.items():
        arah = efek["arah"]
        if arah not in ("naik_berisiko", "naik_aman"):
            continue

        nilai_berisiko = CONTOH_BERISIKO[field]
        nilai_aman = CONTOH_TIDAK_BERISIKO[field]
        if nilai_berisiko == nilai_aman:
            continue

        # 1. Contoh profil harus urutannya sesuai arah yang diklaim.
        if arah == "naik_berisiko" and nilai_berisiko < nilai_aman:
            konflik.append(
                f"{field}: panduan bilang 'naik = lebih berisiko', tapi contoh "
                f"berisiko memakai nilai {nilai_berisiko} yang lebih rendah dari "
                f"nilai {nilai_aman} pada contoh aman."
            )
        if arah == "naik_aman" and nilai_berisiko > nilai_aman:
            konflik.append(
                f"{field}: panduan bilang 'naik = lebih aman', tapi contoh "
                f"berisiko memakai nilai {nilai_berisiko} yang lebih tinggi dari "
                f"nilai {nilai_aman} pada contoh aman."
            )

        # 2. Model harus berpihak pada arah yang diklaim di antara kedua nilai.
        rendah, tinggi = sorted((nilai_berisiko, nilai_aman))
        risiko_rendah, risiko_tinggi = ukur_dua_ujung(field, rendah, tinggi)
        selisih = risiko_tinggi - risiko_rendah
        if arah == "naik_berisiko" and selisih < -TOLERANSI_NOISE:
            konflik.append(
                f"{field}: panduan bilang 'naik = lebih berisiko', tapi model "
                f"justru lebih aman pada nilai yang lebih tinggi "
                f"(risiko {risiko_rendah:.3f} -> {risiko_tinggi:.3f})."
            )
        if arah == "naik_aman" and selisih > TOLERANSI_NOISE:
            konflik.append(
                f"{field}: panduan bilang 'naik = lebih aman', tapi model "
                f"justru lebih berisiko pada nilai yang lebih tinggi "
                f"(risiko {risiko_rendah:.3f} -> {risiko_tinggi:.3f})."
            )
    return konflik


def ukur_dua_ujung(field: str, rendah: float, tinggi: float):
    """Risiko pada dua nilai field, diukur di profil CONTOH_TIDAK_BERISIKO."""
    from src.prediction import predict_student

    hasil = []
    for nilai in (rendah, tinggi):
        baris = dict(CONTOH_TIDAK_BERISIKO)
        baris[field] = float(nilai)
        hasil.append(predict_student(baris)["probability_risk"])
    return hasil[0], hasil[1]


def main() -> None:
    hasil = {}
    for field in FIELD_BOUNDS:
        terukur = ukur(field)
        hasil[field] = {
            "arah": terukur["arah"],
            "dampak": round(terukur["rentang"], 3),
            "penting": PENTING_TERSIMPAN.get(field, 0.0),
        }
        print(
            f"{field:<32} {hasil[field]['arah']:<16} "
            f"rentang={hasil[field]['dampak']:.3f}"
        )

    print()
    print("FIELD_EFFECT = {")
    for field, efek in sorted(hasil.items(), key=lambda kv: -kv[1]["penting"]):
        print(
            f'    "{field}": {{"arah": "{efek["arah"]}", '
            f'"dampak": {efek["dampak"]}, "penting": {efek["penting"]}}},'
        )
    print("}")

    konflik = cek_konflik_preset(hasil)
    print()
    if konflik:
        print("PERTENTANGAN DENGAN CONTOH PROFIL:")
        for pesan in konflik:
            print(f"  - {pesan}")
    else:
        print("Tidak ada pertentangan antara panduan arah dan contoh profil.")


if __name__ == "__main__":
    main()
