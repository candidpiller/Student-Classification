"""Tests level aplikasi memakai st.testing.v1.AppTest.

Fokus: form prediksi dan tombol contoh/reset. Nilai session state diuji
karena itulah yang membedakan preset benar-benar terpakai atau tidak.
"""
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

pytest.importorskip("streamlit")

from streamlit.testing.v1 import AppTest

from src.form_config import FORM_DEFAULTS, widget_key

APP_PATH = os.path.join(os.path.dirname(__file__), "..", "app.py")
PAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "app_pages")
PAGE_FILES = ["predict.py", "about.py"]


def _number(at, prefix):
    for n in at.number_input:
        if n.label.startswith(prefix):
            return n.value
    raise AssertionError(f"number_input {prefix!r} tidak ditemukan")


def _select(at, label):
    for s in at.selectbox:
        if s.label == label:
            return s.value
    raise AssertionError(f"selectbox {label!r} tidak ditemukan")


def _selectbox(at, label):
    for s in at.selectbox:
        if s.label == label:
            return s
    raise AssertionError(f"selectbox {label!r} tidak ditemukan")


def _button(at, label):
    for b in at.button:
        if b.label == label:
            return b
    raise AssertionError(f"button {label!r} tidak ditemukan")


@pytest.fixture(scope="module")
def at():
    app = AppTest.from_file(APP_PATH, default_timeout=300)
    app.run()
    return app


def test_app_loads_without_exception(at):
    assert not at.exception


def test_preset_risky_applies_to_widgets(at):
    """Tombol 'Contoh berisiko' harus benar-benar mengisi widget."""
    _button(at, "Contoh berisiko").click()
    at.run()

    assert not at.exception
    assert _number(at, "Total click events") == 250.0
    assert _number(at, "Kemiringan klik mingguan") == -3.5
    assert _number(at, "Rata-rata nilai assessment") == 45.0
    assert _select(at, "Kode modul") == "CCC"
    assert _select(at, "Wilayah") == "London Region"


def test_preset_applies_jarak_akses_terakhir(at):
    """Regresi: field ini pernah salah ketik sehingga preset tidak ikut terisi."""
    _button(at, "Contoh berisiko").click()
    at.run()
    assert _number(at, "Hari akses terakhir") == 85.0

    _button(at, "Contoh tidak berisiko").click()
    at.run()
    assert _number(at, "Hari akses terakhir") == 258.0


def test_preset_not_risky_applies_to_widgets(at):
    _button(at, "Contoh tidak berisiko").click()
    at.run()

    assert not at.exception
    assert _number(at, "Total click events") == 3000.0
    assert _number(at, "Kemiringan klik mingguan") == 0.5
    assert _number(at, "Jumlah assessment") == 12.0
    assert _select(at, "Kode modul") == "AAA"
    assert _select(at, "Kode presentasi") == "2013J"
    assert _select(at, "Jenis kelamin") == "F"


def test_reset_mengosongkan_form(at):
    """Reset form mengosongkan input, bukan mengembalikannya ke default."""
    _button(at, "Contoh berisiko").click()
    at.run()
    assert _number(at, "Total click events") == 250.0

    _button(at, "Reset form").click()
    at.run()

    assert not at.exception
    state = at.session_state.filtered_state
    for field in FORM_DEFAULTS:
        assert state[widget_key(field)] is None, f"{field} tidak dikosongkan"

    # Kolom selectbox juga harus kosong, termasuk modul-presentasi yang dirender
    # di luar form.
    assert _select(at, "Kode modul") is None
    assert _select(at, "Kode presentasi") is None


def test_submit_form_kosong_gagal_dengan_pesan_yang_jelas(at):
    """Form kosong tidak boleh crash, dan errornya satu baris untuk daftar field."""
    _button(at, "Reset form").click()
    at.run()
    _button(at, "Prediksi risiko").click()
    at.run()

    assert not at.exception
    assert "Probabilitas berisiko" not in [m.label for m in at.metric]
    belum_disi = [w.value for w in at.warning if "belum diisi" in w.value]
    assert len(belum_disi) == 1, belum_disi
    # Nama field harus pakai label ramah, bukan nama kolom mentah.
    assert "Total click events" in belum_disi[0]


def test_reset_does_not_trigger_prediction(at):
    """Reset hidup di dalam form, jadi ia juga một form_submit_button.

    Kalau tombol reset ikut membuat `submitted` bernilai True, pengguna akan
    mendapat hasil prediksi tepat setelah menekan reset — perilaku yang tidak
    pernah diinginkan.
    """
    _button(at, "Contoh berisiko").click()
    at.run()
    _button(at, "Reset form").click()
    at.run()

    assert not at.exception
    assert "Probabilitas berisiko" not in [m.label for m in at.metric], (
        "tombol Reset form ikut menjalankan prediksi"
    )


def test_predict_button_still_submits(at):
    """Setelah reset dipindah ke dalam form, tombol submit harus tetap jalan."""
    # Fixture `at` dipakai bersama antar-test, dan Reset form kini mengosongkan
    # form. Isi dulu lewat preset supaya test ini tidak bergantung pada sisa
    # state test sebelumnya.
    _button(at, "Contoh berisiko").click()
    at.run()

    _button(at, "Prediksi risiko").click()
    at.run()

    assert not at.exception
    assert "Probabilitas berisiko" in [m.label for m in at.metric]


class TestPanduanArahNilai:
    """Tabel arah nilai dan petunjuk per-field yang tampil di halaman prediksi."""

    def test_expander_panduan_ada(self, at):
        # Penting: Streamlit mengklasifikasikan st.expander yang memakai
        # parameter `icon` sebagai blok "status", jadi ia muncul di at.status,
        # bukan at.expander. Mengaksesnya lewat at.expander selalu kosong.
        labels = [s.label for s in at.status]
        assert "Panduan arah nilai setiap field" in labels

    def test_tabel_memuat_semua_field_numerik(self, at):
        from src.form_config import FIELD_BOUNDS, FIELD_EFFECT

        tabel = at.dataframe[0].value
        assert len(tabel) == len(FIELD_EFFECT) == len(FIELD_BOUNDS)
        assert list(tabel.columns) == [
            "Field", "Arah nilai", "Perubahan risiko", "Penting (%)"
        ]

    def test_tabel_terurut_menurut_pengaruh(self, at):
        tabel = at.dataframe[0].value
        penting = list(tabel["Penting (%)"])
        assert penting == sorted(penting, reverse=True)

    def test_setiap_widget_numerik_punya_petunjuk_arah(self, at):
        from src.form_config import DIRECTION_LABEL, FIELD_EFFECT, FIELD_LABELS

        for nomor in at.number_input:
            field = next(
                (f for f in FIELD_EFFECT
                 if nomor.label.startswith(FIELD_LABELS[f])),
                None,
            )
            assert field is not None, f"tidak ada field cocok untuk {nomor.label!r}"
            assert DIRECTION_LABEL[FIELD_EFFECT[field]["arah"]] in (nomor.help or ""), (
                f"{field}: help widget tidak menyebut arah pengaruhnya"
            )

    def test_field_yang_diabaikan_model_tidak_ditampilkan(self, at):
        assert not any(
            n.label.startswith("Hari terakhir akses") for n in at.number_input
        )

    def test_label_menyesatkan_sudah_diganti(self, at):
        labels = [n.label for n in at.number_input]
        assert any(l.startswith("Hari akses terakhir") for l in labels)
        assert not any(l.startswith("Jarak akses terakhir") for l in labels)


class TestFieldTambahanDiExpander:
    """Field berlabel 'pengaruh kecil' dilipat ke expander, bukan dibuang."""

    def test_expander_field_tambahan_ada(self, at):
        from src.form_config import FIELDS_TAMBAHAN

        labels = [s.label for s in at.status]
        assert any(
            label.startswith("Field tambahan") and str(len(FIELDS_TAMBAHAN)) in label
            for label in labels
        ), labels

    def test_field_tambahan_tetap_dirender(self, at):
        from src.form_config import FIELDS_TAMBAHAN, widget_key

        keys = {n.key for n in at.number_input}
        for field in FIELDS_TAMBAHAN:
            assert widget_key(field) in keys, f"{field} hilang dari form"

    def test_field_tambahan_memang_di_dalam_expander(self, at):
        """Bukan sekadar ada di form, tapi benar-benar berada di dalam expander."""
        from src.form_config import FIELDS_TAMBAHAN, widget_key

        blok = next(
            s for s in at.status
            if s.label.startswith("Field tambahan")
        )
        kunci_di_dalam = _kunci_number_input(blok)
        for field in FIELDS_TAMBAHAN:
            assert widget_key(field) in kunci_di_dalam, (
                f"{field} tidak ada di dalam expander 'Field tambahan'"
            )

    def test_field_tambahan_tidak_ada_di_bagian_utama(self, at):
        """Field tambahan tidak boleh bocor ke form utama."""
        from src.form_config import FIELDS_TAMBAHAN, widget_key

        semua_kunci = {n.key for n in at.number_input}
        kunci_tambahan = {widget_key(f) for f in FIELDS_TAMBAHAN}
        assert kunci_tambahan <= semua_kunci

        # Hitung berapa field yang TIDAK berada di expander: harusnya 18 dari 23.
        blok = next(s for s in at.status if s.label.startswith("Field tambahan"))
        jumlah_dalam = len(_kunci_number_input(blok))
        assert jumlah_dalam == len(FIELDS_TAMBAHAN)
        assert len(semua_kunci) - jumlah_dalam == len(semua_kunci) - len(FIELDS_TAMBAHAN)

    def test_semua_field_tetap_ada_setelah_dilipat(self, at):
        from src.form_config import NUMERIC_FORM_FIELDS

        assert len(at.number_input) == len(NUMERIC_FORM_FIELDS)

    def test_field_expander_ikut_mengubah_prediksi(self, at):
        """Nilai di dalam expander harus tetap sampai ke model.

        Expander menutup, bukan membuang input. Kalau nilai ini tidak ikut,
        prediksi diam-diam dihitung dari default dan form jadi menipu.
        """
        from src.form_config import CONTOH_TIDAK_BERISIKO, FIELDS_TAMBAHAN
        from src.prediction import predict_student

        field = FIELDS_TAMBAHAN[0]
        _button(at, "Contoh tidak berisiko").click()
        at.run()
        _button(at, "Prediksi risiko").click()
        at.run()
        sebelum = _risiko_persen(at)

        nomor = next(n for n in at.number_input if n.key == f"f_{field}")
        nilai_baru = 0.0 if nomor.value > 0 else 1.0
        nomor.set_value(nilai_baru)
        at.run()
        _button(at, "Prediksi risiko").click()
        at.run()
        sesudah = _risiko_persen(at)

        assert abs(sesudah - sebelum) > 1e-4, (
            f"mengubah {field} di dalam expander tidak mengubah prediksi: "
            f"{sebelum} -> {sesudah}"
        )

        # Bandingkan juga dengan jalur resmi.
        row = dict(CONTOH_TIDAK_BERISIKO)
        row[field] = nilai_baru
        resmi = predict_student(row)["probability_risk"] * 100
        assert abs(resmi - sesudah) < 0.01, (resmi, sesudah)

    def test_reset_juga_mengosongkan_field_tambahan(self, at):
        from src.form_config import FIELDS_TAMBAHAN, widget_key

        _button(at, "Contoh berisiko").click()
        at.run()
        _button(at, "Reset form").click()
        at.run()

        state = at.session_state.filtered_state
        for field in FIELDS_TAMBAHAN:
            key = widget_key(field)
            assert state[key] is None, field


def _kunci_number_input(blok) -> set:
    """Kunci widget number_input di seluruh subtree sebuah blok.

    AppTest mengekspos elemennya datar, jadi tidak ada cara untuk tahu sebuah
    widget berada di dalam expander atau tidak selain menelusuri pohonnya.
    """
    terkumpul = set()
    for node in getattr(blok, "children", {}).values():
        kunci = getattr(node, "key", None)
        if kunci is not None and node.__class__.__name__ == "NumberInput":
            terkumpul.add(kunci)
        terkumpul |= _kunci_number_input(node)
    return terkumpul


def _risiko_persen(at):
    """Nilai metrik 'Probabilitas berisiko' dalam persen, sebagai float."""
    teks = next(m.value for m in at.metric if m.label == "Probabilitas berisiko")
    return float(teks.replace("%", "").replace(",", "."))


def test_preset_values_stay_inside_widget_bounds(at):
    """Nilai preset harus valid terhadap batas min/max widget."""
    for label in ("Contoh berisiko", "Contoh tidak berisiko", "Reset form"):
        _button(at, label).click()
        at.run()
        assert not at.exception, f"{label} menghasilkan exception"
        for n in at.number_input:
            lo, hi = getattr(n, "min"), n.max
            if n.value is None:
                # Reset form sengaja mengosongkan kolom, jadi tidak ada nilai
                # yang bisa dibandingkan dengan batas.
                assert label == "Reset form", f"{n.label} kosong di {label}"
                continue
            assert lo <= n.value <= hi, (
                f"{n.label} = {n.value} di luar [{lo}, {hi}]"
            )


def test_form_has_one_widget_per_field():
    """Setiap field form harus punya tepat satu widget.

    AppTest menempelkan rentang min-max ke label number_input, jadi label
    dibandingkan dengan prefix, bukan kesamaan persis.
    """
    from src.form_config import FIELD_LABELS, FORM_DEFAULTS

    at = AppTest.from_file(APP_PATH, default_timeout=300)
    at.run()

    widgets = [n.label for n in at.number_input] + [s.label for s in at.selectbox]
    expected = [FIELD_LABELS[f] for f in FORM_DEFAULTS]

    assert len(widgets) == len(expected)
    assert [w for w in widgets if not any(w.startswith(e) for e in expected)] == []
    assert [e for e in expected if not any(w.startswith(e) for w in widgets)] == []


def test_module_presentation_options_are_filtered():
    """Dropdown presentasi hanya menampilkan kombinasi yang benar-benar ada."""
    from src.prediction import load_module_stats
    from src.preprocessing import presentations_for

    at = AppTest.from_file(APP_PATH, default_timeout=300)
    at.run()

    module = _select(at, "Kode modul")
    presentation = _selectbox(at, "Kode presentasi")
    expected = presentations_for(module, load_module_stats())

    assert list(presentation.options) == expected
    assert presentation.value in expected


def test_switching_module_refilters_presentations():
    at = AppTest.from_file(APP_PATH, default_timeout=300)
    at.run()

    _selectbox(at, "Kode modul").select("CCC").run()

    assert list(_selectbox(at, "Kode presentasi").options) == ["2014B", "2014J"]
    assert _select(at, "Kode presentasi") in ("2014B", "2014J")


def test_no_impossible_pair_is_reachable_from_the_form():
    """Setiap modul yang bisa dipilih harus punya presentasi yang valid."""
    from src.prediction import load_module_stats
    from src.preprocessing import presentations_for

    at = AppTest.from_file(APP_PATH, default_timeout=300)
    at.run()

    module_box = _selectbox(at, "Kode modul")
    for module in module_box.options:
        at2 = AppTest.from_file(APP_PATH, default_timeout=300)
        at2.run()
        _selectbox(at2, "Kode modul").select(module).run()

        assert _select(at2, "Kode presentasi") in presentations_for(
            module, load_module_stats()
        ), f"modul {module} bisa dipilih dengan presentasi yang tidak valid"


@pytest.mark.parametrize("page_file", PAGE_FILES)
def test_page_renders_without_exception(page_file):
    """Setiap halaman harus bisa dirender tanpa error."""
    path = os.path.join(PAGES_DIR, page_file)

    page = AppTest.from_file(path, default_timeout=300)
    page.run()

    assert not page.exception, f"{page_file} gagal dirender: {page.exception}"


def test_navigation_registers_only_predict_and_about():
    """Entry point hanya boleh mendaftarkan dua halaman yang tersisa."""
    source = open(APP_PATH, encoding="utf-8").read()

    for page_file in PAGE_FILES:
        assert f"app_pages/{page_file}" in source, f"{page_file} tidak terdaftar"

    for removed in ("batch.py", "dashboard.py"):
        assert removed not in source, f"{removed} masih terdaftar di app.py"
        assert not os.path.exists(os.path.join(PAGES_DIR, removed)), (
            f"{removed} masih ada di app_pages/"
        )


def test_navbar_is_hidden_and_sidebar_stays_empty():
    """Navbar harus disembunyikan dan tidak ada lagi isi sidebar."""
    source = open(APP_PATH, encoding="utf-8").read()

    assert 'position="hidden"' in source, "navbar belum disembunyikan"
    assert "st.sidebar" not in source, "sidebar masih diisi manual"

    page = AppTest.from_file(APP_PATH, default_timeout=300)
    page.run()

    assert not page.exception
    assert len(page.sidebar) == 0, "sidebar masih punya widget"


def test_every_page_has_its_own_title():
    """Tanpa navbar, tiap halaman harus punya judul sendiri."""
    for page_file, expected in [
        ("predict.py", "Prediksi risiko mahasiswa"),
        ("about.py", "Tentang model"),
    ]:
        page = AppTest.from_file(
            os.path.join(PAGES_DIR, page_file), default_timeout=300
        )
        page.run()

        assert not page.exception
        assert [t.value for t in page.title] == [expected], (
            f"{page_file} tidak punya judul '{expected}'"
        )


def test_all_material_icons_are_valid():
    """Nama icon Material harus benar; salah nama = crash saat render."""
    import pathlib
    import re

    from streamlit.string_util import validate_material_icon

    root = pathlib.Path(__file__).resolve().parent.parent
    files = [root / "app.py", *sorted((root / "app_pages").glob("*.py"))]

    invalid = []
    for path in files:
        source = path.read_text(encoding="utf-8")
        for name in set(re.findall(r":material/([a-z0-9_]+):", source)):
            try:
                validate_material_icon(f":material/{name}:")
            except Exception:
                invalid.append(f"{path.name}: :material/{name}:")

    assert not invalid, f"icon Material tidak valid: {invalid}"


def test_about_page_lists_model_artifacts():
    page = AppTest.from_file(
        os.path.join(PAGES_DIR, "about.py"), default_timeout=300
    )
    page.run()

    cells = [
        str(value)
        for frame in page.dataframe
        for value in frame.value.to_numpy().ravel()
    ]

    assert any("04_final_model.pkl" in cell for cell in cells)


def _submitted_page(tmp_path, session_patch: dict | None = None):
    """Jalankan predict.py dengan tombol submit dipaksa terpicu.

    AppTest bisa mengklik st.form_submit_button, tapi menjadikannya cara paling
    sederhana untuk menguji jalur submit: penjaga `if not submitted: st.stop()`
    diganti `submitted = True` supaya model tidak dipanggil berulang kali.
    Ini tempat bug seperti field yang tidak terbaca dari form pernah muncul.
    """
    source = open(os.path.join(PAGES_DIR, "predict.py"), encoding="utf-8").read()
    patched, count = re.subn(
        r"if not submitted:\s*\n\s*st\.stop\(\)",
        "submitted = True",
        source,
    )
    assert count == 1, "penjaga `if not submitted: st.stop()` tidak ditemukan"

    target = tmp_path / "predict_submitted.py"
    target.write_text(patched, encoding="utf-8")

    page = AppTest.from_file(str(target), default_timeout=300)
    if session_patch:
        for key, value in session_patch.items():
            page.session_state[key] = value
    page.run()
    return page


def test_submit_path_runs_without_exception(tmp_path):
    """Regresi: jalur submit pernah gagal karena field di luar form tidak terbaca."""
    page = _submitted_page(tmp_path)

    assert not page.exception, f"submit gagal: {[e.message for e in page.exception]}"
    assert "Probabilitas berisiko" in [m.label for m in page.metric], (
        "halaman tidak menampilkan hasil prediksi, patch submit kemungkinan gagal"
    )


def test_submit_path_shows_prediction(tmp_path):
    page = _submitted_page(tmp_path)

    labels = [m.label for m in page.metric]
    assert "Probabilitas berisiko" in labels
    assert any("skor" in label.lower() for label in labels)


def test_submit_path_with_risky_preset(tmp_path):
    from src.form_config import CONTOH_BERISIKO, widget_key

    page = _submitted_page(
        tmp_path,
        {widget_key(f): v for f, v in CONTOH_BERISIKO.items()},
    )

    assert not page.exception
    labels = [m.label for m in page.metric]
    assert "Probabilitas berisiko" in labels


def test_form_repairs_impossible_presentation_in_session_state(tmp_path):
    """Nilai presentasi yang tidak valid di session state harus dinormalkan.

    Praktik ini yang membuat pasangan modul-presentasi palsu tidak dapat dicapai
    lewat form, walau session state sudah berisi kombinasi yang tidak pernah ada.
    """
    from src.form_config import FORM_DEFAULTS, widget_key
    from src.prediction import load_module_stats
    from src.preprocessing import presentations_for

    patch = {widget_key(f): v for f, v in FORM_DEFAULTS.items()}
    patch[widget_key("code_module")] = "CCC"
    patch[widget_key("code_presentation")] = "2013B"

    page = _submitted_page(tmp_path, patch)

    assert not page.exception
    assert _select(page, "Kode presentasi") in presentations_for("CCC", load_module_stats())
    assert "Probabilitas berisiko" in [m.label for m in page.metric]
