"""
Script untuk generate feature_ranges.json dari data training OULAD.
Jalankan di Kaggle notebook atau local yang memiliki akses ke data OULAD.

Cara pakai:
    1. Jalankan notebook training (ebm-ctgan-fixed-cl.ipynb) sampai Cell 30
    2. Jalankan script ini
    3. Copy output feature_ranges.json ke folder models/
"""
import json
import os
import sys

import kagglehub
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import FEATURE_ORDER, NUMERIC_COLS

# Download dataset
path = kagglehub.dataset_download('anlgrbz/student-demographics-online-education-dataoulad')

# Load data
data_info = pd.read_csv(f'{path}/studentInfo.csv')
data_vle = pd.read_csv(f'{path}/studentVle.csv')
data_assessment = pd.read_csv(f'{path}/studentAssessment.csv')

# ===== ASSESSMENT FEATURES =====
fitur_assessment = data_assessment.groupby('id_student').agg({
    'score': ['count', 'mean', 'std', 'min', 'max'],
    'is_banked': 'sum'
}).fillna(0)
fitur_assessment.columns = [
    'jumlah_assessment', 'rata_rata_nilai_assessment', 'std_nilai_assessment',
    'min_nilai_assessment', 'max_nilai_assessment', 'jumlah_assessment_banked'
]

# ===== VLE BASIC FEATURES =====
fitur_vle = data_vle.groupby('id_student').agg({
    'sum_click': ['sum', 'mean', 'std'],
    'date': ['min', 'max', 'nunique']
}).fillna(0)
fitur_vle.columns = [
    'total_click_events', 'rata_rata_click_per_aktivitas', 'std_click_events',
    'hari_pertama_akses', 'hari_terakhir_akses', 'jumlah_hari_akses'
]
fitur_vle['durasi_pembelajaran_hari'] = fitur_vle['hari_terakhir_akses'] - fitur_vle['hari_pertama_akses']

# ===== VLE TEMPORAL FEATURES =====
vle_minmax = data_vle.groupby('id_student')['date'].agg(d_min='min', d_max='max')
vle = data_vle.join(vle_minmax, on='id_student')
vle['span'] = (vle['d_max'] - vle['d_min']).clip(lower=1)
vle['rel_pos'] = (vle['date'] - vle['d_min']) / vle['span']
vle['click_early'] = vle['sum_click'] * (vle['rel_pos'] <= 0.333)
vle['click_mid'] = vle['sum_click'] * ((vle['rel_pos'] > 0.333) & (vle['rel_pos'] <= 0.667))
vle['click_late'] = vle['sum_click'] * (vle['rel_pos'] > 0.667)

period_agg = vle.groupby('id_student').agg(
    klik_awal=('click_early', 'sum'),
    klik_tengah=('click_mid', 'sum'),
    klik_akhir=('click_late', 'sum'),
    total_klik=('sum_click', 'sum'),
    jarak_akses_terakhir=('d_max', 'first')
)
period_agg['tren_klik'] = period_agg['klik_akhir'] / (period_agg['klik_awal'] + 1)
period_agg['rasio_klik_awal'] = period_agg['klik_awal'] / (period_agg['total_klik'] + 1e-9)
period_agg['rasio_klik_akhir'] = period_agg['klik_akhir'] / (period_agg['total_klik'] + 1e-9)
period_agg['periode_puncak_aktivitas'] = period_agg[['klik_awal', 'klik_tengah', 'klik_akhir']].values.argmax(axis=1)

daily_agg = vle.groupby(['id_student', 'date'])['sum_click'].sum().reset_index()
daily_std = daily_agg.groupby('id_student')['sum_click'].std().fillna(0)
period_agg['konsistensi_keterlibatan'] = 1 / (daily_std + 1)

vle['week_bin'] = np.floor((vle['date'] - vle['d_min']) / 7).astype(int)
weekly_agg = vle.groupby(['id_student', 'week_bin'])['sum_click'].sum().reset_index()

def _slope(g):
    if len(g) < 2:
        return 0.0
    return np.polyfit(g['week_bin'], g['sum_click'], 1)[0]

student_span = vle.groupby('id_student')['span'].first()
students_14d = student_span[student_span >= 14].index
weekly_long = weekly_agg[weekly_agg['id_student'].isin(students_14d)]
slopes = weekly_long.groupby('id_student').apply(_slope)
slopes.name = 'kemiringan_klik_mingguan'
period_agg = period_agg.join(slopes)
period_agg['kemiringan_klik_mingguan'] = period_agg['kemiringan_klik_mingguan'].fillna(0)

fitur_temporal = period_agg[['klik_awal', 'klik_tengah', 'klik_akhir', 'tren_klik',
    'rasio_klik_awal', 'rasio_klik_akhir', 'periode_puncak_aktivitas',
    'jarak_akses_terakhir', 'konsistensi_keterlibatan', 'kemiringan_klik_mingguan']].reset_index()

# ===== MERGE ALL =====
data_gabungan = data_info.copy()
data_gabungan = data_gabungan.merge(fitur_assessment.reset_index(), on='id_student', how='left')
data_gabungan = data_gabungan.merge(fitur_vle.reset_index(), on='id_student', how='left')
data_gabungan = data_gabungan.merge(fitur_temporal, on='id_student', how='left')
numeric_columns = data_gabungan.select_dtypes(include=[np.number]).columns
data_gabungan[numeric_columns] = data_gabungan[numeric_columns].fillna(0)

# ===== DERIVED FEATURES =====
data_gabungan['click_per_day'] = data_gabungan['total_click_events'] / (data_gabungan['jumlah_hari_akses'] + 1)
data_gabungan['nilai_consistency'] = 1 / (data_gabungan['std_nilai_assessment'] + 1)
data_gabungan['early_engagement'] = data_gabungan['total_click_events'] / (data_gabungan['durasi_pembelajaran_hari'] + 1)
data_gabungan['nilai_x_assessment'] = data_gabungan['rata_rata_nilai_assessment'] * data_gabungan['jumlah_assessment']
data_gabungan['engagement_per_assessment'] = data_gabungan['total_click_events'] / (data_gabungan['jumlah_assessment'] + 1)
data_gabungan['tren_x_konsistensi'] = data_gabungan['tren_klik'] * data_gabungan['nilai_consistency']

# ===== DIFFICULTY (training only — use all data for ranges) =====
mapping_target = {'Pass': 1, 'Fail': 0, 'Withdrawn': 0, 'Distinction': 1}
data_gabungan['target_binary'] = data_gabungan['final_result'].map(mapping_target).fillna(0)

module_pass_rate = data_gabungan.groupby('code_module')['target_binary'].mean()
pres_pass_rate = data_gabungan.groupby(['code_module', 'code_presentation'])['target_binary'].mean()
global_pr = data_gabungan['target_binary'].mean()

data_gabungan['skor_kesulitan_modul'] = 1 - data_gabungan['code_module'].map(module_pass_rate).fillna(global_pr)
pres_key = list(zip(data_gabungan['code_module'], data_gabungan['code_presentation']))
data_gabungan['skor_kesulitan_presentasi'] = 1 - pd.Series(pres_key, index=data_gabungan.index).map(pres_pass_rate).fillna(global_pr)
data_gabungan['skor_disesuaikan_kesulitan'] = data_gabungan['rata_rata_nilai_assessment'] * (1 - data_gabungan['skor_kesulitan_modul'])

# ===== GENERATE RANGES =====
DISCRETE = {"periode_puncak_aktivitas", "num_of_prev_attempts"}
RATIO = {
    "rasio_klik_awal", "rasio_klik_akhir", "konsistensi_keterlibatan",
    "tren_klik", "skor_kesulitan_modul", "skor_kesulitan_presentasi",
    "skor_disesuaikan_kesulitan",
}

feature_ranges = {}
for feat in NUMERIC_COLS:
    if feat in data_gabungan.columns:
        col = data_gabungan[feat]
        if feat in DISCRETE:
            step = 1
        elif feat in RATIO:
            step = 0.01
        else:
            step = 0.1
        feature_ranges[feat] = {
            "type": "numeric",
            "min": round(float(col.min()), 2),
            "max": round(float(col.max()), 2),
            "mean": round(float(col.mean()), 4),
            "median": round(float(col.median()), 4),
            "std": round(float(col.std()), 4),
            "step": step,
        }

output = {
    "dataset": "OULAD",
    "model": "Explainable Boosting Machine",
    "balancing": "CTGAN",
    "target": "target_binary",
    "target_mapping": {"Fail": 0, "Withdrawn": 0, "Pass": 1, "Distinction": 1},
    "threshold": 0.5,
    "n_features": len(FEATURE_ORDER),
    "feature_names": FEATURE_ORDER,
    "features": feature_ranges,
}

with open("feature_ranges.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print("feature_ranges.json berhasil dibuat!")
print(f"Jumlah fitur numerik: {len(feature_ranges)} / {len(NUMERIC_COLS)}")
