"""
Operasi session state dan perakitan input form — tanpa memanggil Streamlit.

Dulu logika ini menumpang di ``app_pages/predict.py`` sehingga hanya bisa diuji
lewat AppTest. Sekarang bisa diuji sebagai fungsi biasa.
"""
from collections.abc import MutableMapping

from src.field_spec import FORM_DEFAULTS, MODULE_FIELDS, widget_key

PENDING_PRESET_KEY = "pending_preset"


def seed_widget_state(
    state: MutableMapping,
    defaults: dict | None = None,
) -> None:
    """Isi session state dengan default hanya untuk widget yang belum ada."""
    for field, value in (defaults or FORM_DEFAULTS).items():
        state.setdefault(widget_key(field), value)


def apply_widget_values(state: MutableMapping, values: dict) -> None:
    """Terapkan nilai (mis. preset) ke session state widget."""
    for field, value in values.items():
        state[widget_key(field)] = value


def request_preset(state: MutableMapping, values: dict) -> None:
    """Simpan preset yang akan diterapkan pada rerun berikutnya."""
    state[PENDING_PRESET_KEY] = values


def apply_pending_preset(state: MutableMapping) -> dict | None:
    """Terapkan preset tertunda, lalu hapus dari session state.

    Tombol preset berada di luar form dan memicu rerun. Nilai widget baru bisa
    diubah sebelum widget dirender, jadi preset dititipkan dulu lewat
    ``request_preset`` dan baru dipakai di awal render berikutnya.
    """
    values = state.pop(PENDING_PRESET_KEY, None)
    if values is not None:
        apply_widget_values(state, values)
    return values


def build_raw_input(
    form_values: dict,
    code_module: str | None,
    code_presentation: str | None,
    fields: list[str] | tuple[str, ...] | None = None,
) -> dict:
    """Gabungkan nilai widget di dalam form dengan modul/presentasi di luar form."""
    raw_input = {
        field: form_values.get(field)
        for field in (fields or FORM_DEFAULTS)
        if field not in MODULE_FIELDS
    }
    raw_input["code_module"] = code_module
    raw_input["code_presentation"] = code_presentation
    return raw_input


def missing_raw_fields(
    raw_input: dict,
    fields: list[str] | tuple[str, ...] | None = None,
) -> list[str]:
    """Field yang seharusnya ikut terkirim tetapi tidak ada di ``raw_input``."""
    return [field for field in (fields or FORM_DEFAULTS) if field not in raw_input]
