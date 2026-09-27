"""Halaman prediksi individual — form input satu mahasiswa."""
import pandas as pd
import streamlit as st

from src.explanation import get_local_explanation
from src.form_config import (
    CONTOH_BERISIKO, CONTOH_TIDAK_BERISIKO, FIELD_BOUNDS, FIELD_HELP,
    FORM_DEFAULTS, FORM_SECTIONS, MODULE_FIELDS, PRESETS, SELECT_OPTIONS,
    field_label, widget_key,
)
from src.prediction import (
    artefak_siap, load_feature_ranges, load_label_encoders, load_module_stats,
    predict_student,
)
from src.preprocessing import (
    build_feature_row, encode_categoricals, presentations_for,
)
from src.validation import validate_input

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
        st.session_state["pending_preset"] = CONTOH_BERISIKO
        st.rerun()
with preset_aman_col:
    if st.button("Contoh tidak berisiko", width="stretch", key="preset_aman"):
        st.session_state["pending_preset"] = CONTOH_TIDAK_BERISIKO
        st.rerun()

st.caption(
    "Isi data mahasiswa, lalu tekan tombol prediksi. Hasil dilengkapi "
    "penjelasan lokal dari model EBM."
)

# Default form hanya perlu di-seed sekali; setelah itu session state yang dipakai.
for field, default in FORM_DEFAULTS.items():
    st.session_state.setdefault(widget_key(field), default)

pending = st.session_state.pop("pending_preset", None)
if pending is not None:
    for field, value in pending.items():
        st.session_state[widget_key(field)] = value

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
        help=FIELD_HELP.get("code_module"),
        key=widget_key("code_module"),
    )
with presentation_col:
    available_presentations = presentations_for(code_module, module_stats)
    current = st.session_state[widget_key("code_presentation")]
    if current not in available_presentations:
        st.session_state[widget_key("code_presentation")] = available_presentations[0]
    code_presentation = st.selectbox(
        field_label("code_presentation"),
        available_presentations,
        help=FIELD_HELP.get("code_presentation"),
        key=widget_key("code_presentation"),
    )

st.caption(
    f"Pass rate modul {code_module}: "
    f"{module_stats['module_pass_rate'].get(code_module, float('nan')):.1%} | "
    f"Pass rate modul + presentasi: "
    f"{module_stats['presentation_pass_rate'].get(f'{code_module}_{code_presentation}', float('nan')):.1%}"
    if module_stats
    else "Statistik modul tidak tersedia, skor kesulitan memakai nilai default global."
)


def render_field(field: str):
    """Render satu widget sesuai tipe datanya."""
    label = field_label(field)
    key = widget_key(field)

    if field in SELECT_OPTIONS:
        return st.selectbox(
            label,
            SELECT_OPTIONS[field],
            help=FIELD_HELP.get(field),
            key=key,
        )

    low, high, step = FIELD_BOUNDS[field]
    return st.number_input(
        label,
        min_value=low,
        max_value=high,
        step=step,
        help=FIELD_HELP.get(field),
        key=key,
    )


form_values: dict = {}

with st.form("prediction_form"):
    for title, fields in FORM_SECTIONS:
        st.subheader(title, anchor=False)

        buckets: list[list[str]] = [[] for _ in range(3)]
        for position, field in enumerate(fields):
            buckets[position % 3].append(field)

        for column, bucket in zip(st.columns(3), buckets):
            with column:
                for field in bucket:
                    form_values[field] = render_field(field)

    submitted = st.form_submit_button(
        "Prediksi risiko", icon=":material/search:", type="primary", width="stretch"
    )

# Tepat di bawah tombol submit, lebarnya sama agar rata dengan form.
if st.button("Reset form", width="stretch"):
    st.session_state["pending_preset"] = PRESETS["Reset form"]
    st.rerun()

if not submitted:
    st.stop()

raw_input = {
    field: form_values[field]
    for field in FORM_DEFAULTS
    if field not in MODULE_FIELDS
}
raw_input["code_module"] = code_module
raw_input["code_presentation"] = code_presentation

missing_fields = [f for f in FORM_DEFAULTS if f not in raw_input]
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
    st.error(
        "Artefak model belum ditemukan di folder `models/`. Pastikan file "
        "`04_final_model.pkl`, `03_scaler.pkl`, dan `label_encoders.pkl` ada."
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

            with st.expander("Rincian faktor", icon=":material/list:"):
                for position, item in enumerate(explanation, 1):
                    st.markdown(
                        f"{position}. **{item['feature']}** — "
                        f"{item['direction']} ({item['score']:+.4f})"
                    )
        else:
            st.warning("Penjelasan lokal tidak tersedia.", icon=":material/error:")

    st.caption(
        "Prediksi ini adalah keluaran model machine learning, bukan keputusan "
        "akademik final."
    )

with st.expander("Skor kesulitan yang dihitung otomatis", icon=":material/functions:"):
    st.caption(
        f"Tiga fitur kesulitan dihitung dari `module_stats.json` memakai modul "
        f"**{code_module}** dan presentasi **{code_presentation}**, bukan diisi "
        "manual. Formula: `1 - pass rate`."
    )

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
