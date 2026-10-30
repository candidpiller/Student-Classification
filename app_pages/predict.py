"""Halaman prediksi individual — form input satu mahasiswa."""
import pandas as pd
import streamlit as st

from src.artifacts import (
    artefak_hilang, artefak_siap, load_feature_ranges, load_label_encoders,
    load_module_stats,
)
from src.explanation import get_local_explanation
from src.field_effect import FIELDS_TAMBAHAN, effect_rows, field_help
from src.field_spec import (
    FIELD_BOUNDS, FORM_SECTIONS, SELECT_OPTIONS, field_label, widget_key,
)
from src.form_state import (
    apply_pending_preset, build_raw_input, missing_raw_fields, request_preset,
    seed_widget_state,
)
from src.prediction import predict_student
from src.preprocessing import build_feature_row, encode_categoricals, presentations_for
from src.presets import CONTOH_BERISIKO, CONTOH_TIDAK_BERISIKO, FORM_KOSONG
from src.validation import validate_input

# Placeholder form yang kosong. value=None + placeholder membuat kolom tampil
# kosong tanpa mengisi angka nol yang diam-diam ikut terkirim ke model.
PLACEHOLDER_ISI = "Isi nilai"
PLACEHOLDER_PILIH = "Pilih salah satu"

# Navbar disembunyikan, jadi setiap halaman punya judul sendiri. Judul dan
# tombol preset berbagi satu baris rata kanan, selaras dasar dengan judul.
# anchor=False menyembunyikan ikon tautan yang muncul saat hover di kanan heading.
judul_col, preset_risiko_col, preset_aman_col = st.columns(
    [4, 1, 1], vertical_alignment="bottom"
)
with judul_col:
    st.title("Prediksi risiko mahasiswa", anchor=False)
with preset_risiko_col:
    if st.button("Contoh berisiko", width="stretch", key="preset_berisiko"):
        request_preset(st.session_state, CONTOH_BERISIKO)
        st.rerun()
with preset_aman_col:
    if st.button("Contoh tidak berisiko", width="stretch", key="preset_aman"):
        request_preset(st.session_state, CONTOH_TIDAK_BERISIKO)
        st.rerun()

st.caption(
    "Isi data mahasiswa, lalu tekan tombol prediksi. Hasil dilengkapi "
    "penjelasan lokal dari model EBM."
)

with st.expander("Panduan arah nilai setiap field", icon=":material/help:"):
    st.caption(
        "Nilai yang lebih tinggi tidak selalu berarti risiko lebih rendah. "
        "Arah diukur langsung dari model: satu field dinaikkan sepanjang "
        "rentangnya (21 titik) sementara field lain ditahan pada profil "
        "contoh tidak berisiko, lalu bentuk respons risikonya diamati dari "
        "seluruh kurva. Jadi ini efek marginal satu field, bukan perbandingan "
        "dua profil."
    )
    st.dataframe(
        effect_rows(),
        width="stretch",
        hide_index=True,
        column_config={
            "Field": st.column_config.TextColumn("Field", width="medium"),
            "Arah nilai": st.column_config.TextColumn("Arah nilai", width="medium"),
            "Perubahan risiko": st.column_config.ProgressColumn(
                "Perubahan risiko",
                min_value=0.0,
                max_value=1.0,
                format="%.2f",
                help=(
                    "Rentang probabilitas risiko: tertinggi dikurangi "
                    "terendah sepanjang rentang nilai field."
                ),
            ),
            "Penting (%)": st.column_config.ProgressColumn(
                "Penting (%)",
                min_value=0.0,
                max_value=20.0,
                format="%.1f%%",
                help="Persentase term importance EBM.",
            ),
        },
    )
    st.caption(
        "Catatan: hubungan ini bukan kausal dan saling tumpang tindih. "
        "Mengubah satu field ikut menggeser fitur turunan, jadi jangan dibaca "
        "sebagai kontribusi per field secara terpisah. Field non-monoton hanya "
        "menggambarkan bentuk responsnya, bukan aturan arah. Dua contoh "
        "profil di aplikasi berbeda di puluhan field sekaligus, jadi "
        "risikonya tidak boleh disimpulkan dari perbandingan keduanya."
    )

# Default form hanya perlu di-seed sekali; setelah itu session state yang dipakai.
seed_widget_state(st.session_state)
apply_pending_preset(st.session_state)

feature_ranges = load_feature_ranges()
module_stats = load_module_stats()

# Dua field ini dirender di luar form: opsi presentasi harus bisa ikut berubah
# begitu modul diganti, sedangkan widget di dalam st.form tidak memicu rerun.
st.subheader("Modul yang diambil", anchor=False)
module_col, presentation_col = st.columns(2)
with module_col:
    code_module = st.selectbox(
        field_label("code_module"),
        SELECT_OPTIONS["code_module"],
        help=field_help("code_module"),
        key=widget_key("code_module"),
        index=None,
        placeholder=PLACEHOLDER_PILIH,
    )
with presentation_col:
    available_presentations = presentations_for(code_module, module_stats)
    current = st.session_state[widget_key("code_presentation")]
    # Pilihan otomatis hanya berlaku setelah modul dipilih. Tanpa penjaga ini,
    # modul kosong akan langsung memaksa presentasi terisi lagi sehingga form
    # tidak pernah benar-benar kosong.
    if code_module and current not in available_presentations:
        st.session_state[widget_key("code_presentation")] = available_presentations[0]
    code_presentation = st.selectbox(
        field_label("code_presentation"),
        available_presentations,
        help=field_help("code_presentation"),
        key=widget_key("code_presentation"),
        index=None,
        placeholder=PLACEHOLDER_PILIH,
    )

if not module_stats:
    st.caption(
        "Statistik modul tidak tersedia, skor kesulitan memakai nilai default global."
    )
elif code_module and code_presentation:
    st.caption(
        f"Pass rate modul {code_module}: "
        f"{module_stats['module_pass_rate'].get(code_module, float('nan')):.1%} | "
        f"Pass rate modul + presentasi: "
        f"{module_stats['presentation_pass_rate'].get(f'{code_module}_{code_presentation}', float('nan')):.1%}"
    )
else:
    st.caption("Pilih kode modul dan presentasi untuk melihat pass rate.")


def render_field(field: str):
    """Render satu widget sesuai tipe datanya."""
    label = field_label(field)
    key = widget_key(field)

    if field in SELECT_OPTIONS:
        return st.selectbox(
            label,
            SELECT_OPTIONS[field],
            help=field_help(field),
            key=key,
            index=None,
            placeholder=PLACEHOLDER_PILIH,
        )

    low, high, step = FIELD_BOUNDS[field]
    return st.number_input(
        label,
        min_value=low,
        max_value=high,
        step=step,
        help=field_help(field),
        key=key,
        value=None,
        placeholder=PLACEHOLDER_ISI,
    )


form_values: dict = {}


def render_field_group(fields: list[str]) -> None:
    """Render sekumpulan field dalam tiga kolom, isi form_values."""
    buckets: list[list[str]] = [[] for _ in range(3)]
    for position, field in enumerate(fields):
        buckets[position % 3].append(field)

    for column, bucket in zip(st.columns(3), buckets):
        with column:
            for field in bucket:
                form_values[field] = render_field(field)


with st.form("prediction_form"):
    for title, fields in FORM_SECTIONS:
        st.subheader(title, anchor=False)
        # Field berlabel "pengaruh kecil" dipindah ke expander di bawah, supaya
        # bagian utama tidak dipenuhi field yang pengaruhnya kecil.
        utama = [f for f in fields if f not in FIELDS_TAMBAHAN]
        render_field_group(utama)

    # Field di expander TETAP bagian dari form, jadi nilainya ikut terkirim saat
    # submit. Expander ini menutup, bukan membuang input.
    with st.expander(
        f"Field tambahan ({len(FIELDS_TAMBAHAN)}) -- pengaruh kecil", icon=":material/expand_more:"
    ):
        st.caption(
            "Field di sini tetap dipakai model, jadi nilainya ikut dihitung. "
            "Hanya rentang risikonya yang kecil, jadi arahnya tidak berarti "
            "dan tidak perlu dibuka kecuali memang perlu menyetelnya."
        )
        render_field_group(FIELDS_TAMBAHAN)

    submitted = st.form_submit_button(
        "Prediksi risiko", icon=":material/search:", type="primary", width="stretch"
    )
    # Widget biasa di dalam st.form tidak memicu rerun, jadi tombol reset juga
    # harus berupa form_submit_button agar bisa diklik. Keduanya terpisah key,
    # sehingga hanya tombol yang diklik yang bernilai True.
    reset_clicked = st.form_submit_button("Reset form", width="stretch")

if reset_clicked:
    request_preset(st.session_state, FORM_KOSONG)
    st.rerun()

if not submitted:
    st.stop()

raw_input = build_raw_input(form_values, code_module, code_presentation)

missing_fields = missing_raw_fields(raw_input)
if missing_fields:
    st.error(f"Field berikut tidak terbaca dari form: {', '.join(missing_fields)}")
    st.stop()

is_valid, errors = validate_input(raw_input, feature_ranges, module_stats)

if not is_valid:
    st.error("Ada data yang belum valid. Periksa kembali input Anda.")
    for message in errors:
        st.warning(message)
    st.stop()

if not artefak_siap():
    hilang = ", ".join(f"`{name}`" for name in artefak_hilang())
    st.error(
        f"Artefak model belum ditemukan di folder `models/`. Pastikan file {hilang} ada."
    )
    st.stop()

result_holder = st.container()
with st.spinner("Menganalisis data mahasiswa..."):
    result = predict_student(raw_input)
    row_lengkap = build_feature_row(raw_input, module_stats)

# Slot hasil dicadangkan lebih dulu supaya tabel di bawah tidak ter-reset.
with result_holder:
    at_risk = result["prediction"] == 0

    header, probabilities = st.columns([1, 2], gap="large")
    with header:
        if at_risk:
            st.error("Berisiko", icon=":material/warning:")
        else:
            st.success("Tidak berisiko", icon=":material/check_circle:")

        st.metric(
            "Probabilitas berisiko",
            f"{result['probability_risk'] * 100:.2f}%",
        )
        st.metric(
            "Probabilitas tidak berisiko",
            f"{result['probability_not_risk'] * 100:.2f}%",
        )
        st.progress(float(result["probability_risk"]))
        st.caption(f"Threshold: {result['threshold'] * 100:.0f}%")

    with probabilities:
        st.markdown("**Faktor yang berkontribusi terhadap prediksi**")
        st.caption(
            "Skor term interaksi model sudah digabung ke fitur penyusunnya, "
            "jadi tiap fitur tampil satu baris."
        )
        explanation = get_local_explanation(result["X_scaled"], result["prediction"])

        if explanation:
            features = [item["feature"] for item in explanation]
            scores = [item["score"] for item in explanation]
            chart = pd.DataFrame({
                "Mendukung berisiko": [s if s < 0 else 0.0 for s in scores],
                "Mendukung tidak berisiko": [s if s > 0 else 0.0 for s in scores],
            }, index=features)

            st.bar_chart(
                chart,
                horizontal=True,
                sort=False,
                height=min(520, max(240, 34 * len(features) + 90)),
                color=["red", "green"],
                x_label="Skor kontribusi",
            )
        else:
            st.warning("Penjelasan lokal tidak tersedia.", icon=":material/error:")

# Tabel rincian dibuat selebar halaman, sejajar dengan dua expander detail di
# bawahnya, supaya ketiganya punya lebar dan indentasi yang sama.
if explanation:
    with st.expander("Rincian faktor", icon=":material/list:"):
        st.dataframe(
            pd.DataFrame({
                "Peringkat": range(1, len(explanation) + 1),
                "Fitur": [item["feature"] for item in explanation],
                "Arah": [item["direction"] for item in explanation],
                "Skor kontribusi": [item["score"] for item in explanation],
            }),
            width="stretch",
            hide_index=True,
            column_config={
                "Peringkat": st.column_config.NumberColumn(
                    "Peringkat", format="%d", width="small"
                ),
                "Arah": st.column_config.TextColumn("Arah", width="medium"),
                "Skor kontribusi": st.column_config.NumberColumn(
                    "Skor kontribusi",
                    format="%+.4f",
                    help=(
                        "Nilai negatif mendorong ke risiko, nilai "
                        "positif mendorong ke tidak berisiko."
                    ),
                ),
            },
        )

with st.expander("Skor kesulitan yang dihitung otomatis", icon=":material/functions:"):
    rate_modul, rate_pres, rate_global = st.columns(3)
    if module_stats:
        rate_modul.metric(
            "Pass rate modul",
            f"{module_stats['module_pass_rate'].get(code_module, float('nan')):.1%}",
        )
        rate_pres.metric(
            "Pass rate presentasi",
            f"{module_stats['presentation_pass_rate'].get(f'{code_module}_{code_presentation}', float('nan')):.1%}",
        )
        rate_global.metric(
            "Pass rate global", f"{module_stats['global_pass_rate']:.1%}"
        )
    else:
        for column in (rate_modul, rate_pres, rate_global):
            column.metric("Pass rate", "-")

    skor_modul, skor_pres, skor_disesuaikan = st.columns(3)
    skor_modul.metric(
        "Skor kesulitan modul", f"{row_lengkap['skor_kesulitan_modul']:.4f}"
    )
    skor_pres.metric(
        "Skor kesulitan presentasi",
        f"{row_lengkap['skor_kesulitan_presentasi']:.4f}",
    )
    skor_disesuaikan.metric(
        "Skor kesulitan disesuaikan",
        f"{row_lengkap['skor_disesuaikan_kesulitan']:.2f}",
    )

with st.expander("Lihat 40 fitur yang dikirim ke model", icon=":material/data_object:"):
    encoded = encode_categoricals(row_lengkap, load_label_encoders())
    st.dataframe(
        pd.DataFrame([encoded]),
        hide_index=True,
        width="stretch",
    )
