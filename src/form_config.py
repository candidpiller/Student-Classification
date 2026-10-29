"""
API publik konfigurasi form.

Modul ini adalah fasad tipis di atas tiga modul yang lebih fokus:

- ``src.field_spec``   — default, batas, label, help, dan section form.
- ``src.field_effect`` — arah dan besaran pengaruh tiap field.
- ``src.presets``      — contoh profil dan form kosong.

Nama-nama lama tetap di-ekspor dari sini supaya halaman dan test yang sudah ada
tidak perlu berubah sekaligus. ``validate_form_config()`` menjaga agar ketiga
modul itu tetap konsisten satu sama lain.
"""
from src.config import (
    AMBANG_EFFECT,
    CATEGORICAL_COLS,
    FEATURE_ORDER,
    REQUIRED_INPUT_FIELDS,
)
from src.field_effect import (
    DIRECTION_LABEL,
    FIELD_EFFECT,
    FIELDS_TAMBAHAN,
    effect_problems,
    effect_rows,
    field_effect,
    field_help,
)
from src.field_spec import (
    FIELD_BOUNDS,
    FIELD_HELP,
    FIELD_LABELS,
    FORM_DEFAULTS,
    FORM_SECTIONS,
    MODULE_FIELDS,
    NON_MODEL_FORM_FIELDS,
    NUMERIC_FORM_FIELDS,
    SELECT_OPTIONS,
    field_label,
    widget_key,
)
from src.presets import (
    CONTOH_BERISIKO,
    CONTOH_TIDAK_BERISIKO,
    FORM_KOSONG,
    PRESETS,
)

__all__ = [
    "AMBANG_EFFECT",
    "CONTOH_BERISIKO",
    "CONTOH_TIDAK_BERISIKO",
    "DIRECTION_LABEL",
    "FIELD_BOUNDS",
    "FIELD_EFFECT",
    "FIELD_HELP",
    "FIELD_LABELS",
    "FIELDS_TAMBAHAN",
    "FORM_DEFAULTS",
    "FORM_KOSONG",
    "FORM_SECTIONS",
    "MODULE_FIELDS",
    "NON_MODEL_FORM_FIELDS",
    "NUMERIC_FORM_FIELDS",
    "PRESETS",
    "SELECT_OPTIONS",
    "effect_rows",
    "field_effect",
    "field_help",
    "field_label",
    "validate_form_config",
    "widget_key",
]


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

    problems.extend(effect_problems())

    # Panduan arah nilai dan contoh profil harus sejalan. Untuk field yang
    # berarah monoton, nilai pada preset berisiko harus berada di sisi yang
    # lebih berisiko dibanding preset aman. Kalau tidak, pembaca aplikasi
    # menemukan dua hal yang saling bertentangan.
    for field, efek in FIELD_EFFECT.items():
        if efek["arah"] not in ("naik_berisiko", "naik_aman"):
            continue
        nilai_berisiko = CONTOH_BERISIKO.get(field)
        nilai_aman = CONTOH_TIDAK_BERISIKO.get(field)
        if nilai_berisiko is None or nilai_aman is None:
            continue
        if efek["arah"] == "naik_berisiko" and nilai_berisiko < nilai_aman:
            problems.append(
                f"{field}: arah 'naik_berisiko' bertentangan dengan preset "
                f"(berisiko {nilai_berisiko} lebih kecil dari aman {nilai_aman})"
            )
        if efek["arah"] == "naik_aman" and nilai_berisiko > nilai_aman:
            problems.append(
                f"{field}: arah 'naik_aman' bertentangan dengan preset "
                f"(berisiko {nilai_berisiko} lebih besar dari aman {nilai_aman})"
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
