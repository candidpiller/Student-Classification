'''
Konstanta proyek Student Risk Prediction.
Urutan fitur, kategori, threshold, dan konstanta lainnya.
'''

# 40 fitur akhir — urutan harus identik dengan model.feature_names_in_
FEATURE_ORDER = [
    "gender", "region", "highest_education", "imd_band", "age_band",
    "num_of_prev_attempts", "studied_credits", "disability",
    "rata_rata_sks_modul", "jumlah_mahasiswa_presentasi",
    "jumlah_assessment", "rata_rata_nilai_assessment", "std_nilai_assessment",
    "min_nilai_assessment", "max_nilai_assessment", "jumlah_assessment_banked",
    "total_click_events", "rata_rata_click_per_aktivitas", "std_click_events",
    "hari_pertama_akses", "jumlah_hari_akses", "durasi_pembelajaran_hari",
    "klik_awal", "klik_tengah", "klik_akhir", "tren_klik",
    "rasio_klik_awal", "rasio_klik_akhir", "periode_puncak_aktivitas",
    "jarak_akses_terakhir", "konsistensi_keterlibatan",
    "kemiringan_klik_mingguan", "click_per_day", "early_engagement",
    "nilai_x_assessment", "engagement_per_assessment", "tren_x_konsistensi",
    "skor_kesulitan_modul", "skor_kesulitan_presentasi",
    "skor_disesuaikan_kesulitan",
]

# Fitur turunan yang dihitung otomatis dari input — bukan input user.
DERIVED_FEATURES = [
    "click_per_day", "early_engagement", "nilai_x_assessment",
    "engagement_per_assessment", "tren_x_konsistensi",
    "rasio_klik_awal", "rasio_klik_akhir", "periode_puncak_aktivitas",
]

# Fitur difficulty yang dihitung otomatis dari module_stats.json.
FEATURES_DIFFICULTY = [
    "skor_kesulitan_modul", "skor_kesulitan_presentasi",
    "skor_disesuaikan_kesulitan",
]

# Field yang diisi user pada form prediksi.
REQUIRED_INPUT_FIELDS = [
    c for c in FEATURE_ORDER
    if c not in DERIVED_FEATURES and c not in FEATURES_DIFFICULTY
] + ["code_module", "code_presentation"]

CATEGORICAL_COLS = [
    "gender", "region", "highest_education", "imd_band", "age_band", "disability",
]

NUMERIC_COLS = [c for c in FEATURE_ORDER if c not in CATEGORICAL_COLS]

DEFAULT_CATEGORIES = {
    "gender": ["M", "F"],
    "region": [
        "East Anglian Region", "East Midlands Region", "Ireland",
        "London Region", "North Region", "North Western Region",
        "Scotland", "South East Region", "South Region",
        "South West Region", "Wales", "West Midlands Region",
        "Yorkshire Region",
    ],
    "highest_education": [
        "No Formal quals", "Lower Than A Level", "A Level or Equivalent",
        "HE Qualification", "Post Graduate Qualification",
    ],
    "imd_band": [
        "0-10%", "10-20%", "20-30%", "30-40%", "40-50%",
        "50-60%", "60-70%", "70-80%", "80-90%", "90-100%",
    ],
    "age_band": ["0-35", "35-55", "55+="],
    "disability": ["N", "Y"],
}

CODE_MODULES = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG"]
CODE_PRESENTATIONS = ["2013B", "2013J", "2014B", "2014J"]

THRESHOLD = 0.50

LABEL_MAP = {
    0: "Berisiko",
    1: "Tidak Berisiko",
}

MODEL_METRICS = {
    "Accuracy": "92.73%",
    "AUC-ROC": "0.9764",
    "PR-AUC": "0.9668",
    "F1-Score (Macro)": "92.72%",
    "Recall Kelas 0 (Gagal)": "90.41%",
    "Recall Kelas 1 (Lulus)": "95.32%",
}

MODEL_INFO = {
    "name": "Explainable Boosting Machine (EBM)",
    "balancing": "CTGAN",
    "dataset": "Open University Learning Analytics Dataset (OULAD)",
    "n_features": f"{len(FEATURE_ORDER)} ({len(CATEGORICAL_COLS)} kategorikal + {len(NUMERIC_COLS)} numerik)",
    "threshold": "0.50",
}

GLOBAL_PASS_RATE = 0.472
