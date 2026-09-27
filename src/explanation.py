"""
Modul explanation — EBM local explanation untuk prediksi per mahasiswa.
"""
import logging
from collections import defaultdict

import numpy as np
import pandas as pd

from src.prediction import load_model

logger = logging.getLogger(__name__)

# Pemisah nama term interaksi pada EBM, mis. "a & b".
INTERACTION_SEP = " & "


def get_local_explanation(X_scaled: pd.DataFrame, prediction: int, top_n: int = 10) -> list[dict]:
    """Mengambil top N fitur yang berkontribusi terhadap prediksi."""
    model = load_model()

    try:
        local_exp = model.explain_local(X_scaled, np.array([prediction]))
        data = local_exp.data(0)
        names = list(data["names"])
        scores = list(data["scores"])

        contrib = pd.DataFrame({"feature": names, "score": scores})
        contrib["abs_score"] = contrib["score"].abs()
        contrib = contrib.sort_values("abs_score", ascending=False).head(top_n)

        results = []
        for _, row in contrib.iterrows():
            direction = (
                "Mendukung prediksi Berisiko" if row["score"] < 0
                else "Mendukung prediksi Tidak Berisiko"
            )
            results.append({
                "feature": row["feature"],
                "score": round(float(row["score"]), 4),
                "direction": direction,
            })
        return results
    except Exception:
        logger.exception("Gagal menghitung local explanation EBM.")
        return []


def _as_list(value) -> list:
    """Ambil nilai sebagai list, baik berupa property maupun method."""
    if callable(value):
        value = value()
    return list(np.ravel(np.asarray(value, dtype=object)))


def get_global_importance(top_n: int | None = None) -> pd.DataFrame:
    """Global feature importance dari model EBM.

    Term interaksi (mis. "a & b") dipecah lalu dijumlahkan ke masing-masing
    fitur, lalu dinormalisasi jadi persen terhadap total importance.
    """
    model = load_model()

    try:
        names = _as_list(model.term_names_)
        importances = _as_list(model.term_importances)
        if len(names) != len(importances):
            raise ValueError(
                f"Panjang term_names_ ({len(names)}) tidak sama dengan "
                f"term_importances ({len(importances)})"
            )

        per_feature: dict[str, float] = defaultdict(float)
        for name, value in zip(names, importances):
            for part in str(name).split(INTERACTION_SEP):
                per_feature[part.strip()] += float(value)

        total = sum(per_feature.values())
        if total <= 0:
            return pd.DataFrame(columns=["fitur", "penting"])

        series = pd.Series(per_feature).sort_values(ascending=False)
        frame = pd.DataFrame({
            "fitur": series.index,
            "penting": (series.to_numpy() / total * 100).round(2),
        })
        return frame if top_n is None else frame.head(top_n)
    except Exception:
        logger.exception("Gagal menghitung global feature importance EBM.")
        return pd.DataFrame(columns=["fitur", "penting"])
