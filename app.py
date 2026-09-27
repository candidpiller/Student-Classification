import streamlit as st

st.set_page_config(
    page_title="Prediksi Risiko Mahasiswa",
    page_icon=":material/school:",
    layout="wide",
)

# Hanya dua halaman: prediksi individual dan tentang model.
# position="hidden" menyembunyikan navbar hasil st.navigation, sehingga aplikasi
# tampil sebagai satu halaman penuh tanpa sidebar. Routing antar halaman tetap
# dipakai st.navigation lewat query param (?page=tentang-model), dan tautan
# antar halaman dibuat manual di bawah karena navbar disembunyikan.
PAGES = [
    st.Page(
        "app_pages/predict.py",
        title="Prediksi individual",
        icon=":material/person:",
        url_path="prediksi",
        default=True,
    ),
    st.Page(
        "app_pages/about.py",
        title="Tentang model",
        icon=":material/info:",
        url_path="tentang-model",
    ),
]

page = st.navigation(PAGES, position="hidden")

# Tanpa navbar, tiap halaman butuh satu jalan ke halaman berikutnya. Dicari
# berdasarkan title (unik dan stabil) agar tidak bergantung pada url_path.
halaman_lain = next((p for p in PAGES if p.title != page.title), None)
if halaman_lain is not None:
    st.page_link(
        halaman_lain,
        icon=halaman_lain.icon,
        label=f"Buka {halaman_lain.title}",
    )
    st.write("")

page.run()
