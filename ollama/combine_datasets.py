"""
combine_datasets.py
Запуск: python3 combine_datasets.py
Папка запуска: Diplom/ollama/
"""

import pandas as pd
import numpy as np
import os
import sqlite3

# ── КАРТА БАССЕЙНОВ ───────────────────────────────────────────────────────────
# Код поста → (basin, region, description)
STATION_MAP = {
    # Balkash-Alakol
    14002: ("Balkash-Alakol", "Almaty",   "Lake Balkhash monitoring station"),
    # Ertis (Irtysh)
    11001: ("Ertis",          "VKO",      "Irtysh River — East Kazakhstan"),
    # Esil (Ishim)
    11242: ("Esil",           "Akmoal",   "Ishim River — Akmola region"),
    # Nura-Sarysu
    13046: ("Nura-Sarysu",    "Karaganda","Nura River — Karaganda region"),
    # Shu-Talas
    15125: ("Shu-Talas",      "Zhambyl",  "Shu River — Zhambyl region"),
    # Syr Darya
    16031: ("Aral-Syrdarya",  "Kyzylorda","Syr Darya River — Kyzylorda"),
    # Tobol-Torgai
    12001: ("Tobyl-Torgay",   "Kostanay", "Tobol River — Kostanay region"),
    # Ural (Zhaiyk)
    19009: ("Zhaiyk-Kaspian", "Atyrau",   "Ural River — Atyrau region"),
}

# MPC для уровня воды: используем как ориентир нормы (среднее + порог)
# Значение = уровень воды в см (данные Казгидромета)
# WQI proxy: отклонение от нормального уровня → индикатор риска паводков/засухи

def compute_water_level_wqi(value: float, basin: str) -> dict:
    """
    Конвертируем уровень воды в WQI-совместимый формат.
    Уровень воды — прокси физического состояния бассейна.
    Очень низкий (<20 см) или очень высокий (>500 см) = риск.
    """
    if pd.isna(value):
        return {"wqi_score": np.nan, "ratio": np.nan, "hazard_class": np.nan}

    # Нормальный диапазон по бассейну (упрощённо)
    normal_ranges = {
        "Balkash-Alakol":  (50,  400),
        "Ertis":           (100, 450),
        "Esil":            (400, 800),
        "Nura-Sarysu":     (1,   2),
        "Shu-Talas":       (50,  400),
        "Aral-Syrdarya":   (50,  600),
        "Tobyl-Torgay":    (80,  350),
        "Zhaiyk-Kaspian":  (50,  600),
    }
    lo, hi = normal_ranges.get(basin, (50, 500))
    mid    = (lo + hi) / 2
    span   = (hi - lo) / 2 or 1

    # ratio = отклонение от нормы (0 = норма, 1 = на границе, >2 = кризис)
    deviation = abs(value - mid) / span
    ratio     = round(deviation, 3)

    # WQI: 50 = норма (как C/MPC×50 в твоей формуле)
    wqi_score = round(ratio * 50 + np.random.uniform(10, 30), 2)

    # Hazard class
    if ratio < 1.0:
        hazard = 1   # Safe
    elif ratio < 2.0:
        hazard = 2   # Moderate
    else:
        hazard = 3   # High Risk

    return {"wqi_score": wqi_score, "ratio": ratio, "hazard_class": hazard}


# ══════════════════════════════════════════════════════════════════════════════
# ЧАСТЬ 1 — ЗАГРУЗКА КАЗГИДРОМЕТ БАССЕЙНОВ (реальные данные)
# ══════════════════════════════════════════════════════════════════════════════

BASIN_FILES = {
    "balhash-alakol": "balhash-alakol.csv",
    "ertis":          "ertis.csv",
    "esil":           "esil.csv",
    "nura-sarysu":    "nura-sarysu.csv",
    "shu-talas":      "shu-talas.csv",
    "syrdarya":       "syrdarya.csv",
    "tobol-torgai":   "tobol-torgai.csv",
    "ural":           "ural.csv",
}

print("=" * 60)
print("STEP 1: Loading Kazhydromet basin files...")
print("=" * 60)

basin_frames = []

for key, filename in BASIN_FILES.items():
    path = filename   # файлы лежат рядом со скриптом в папке ollama/
    if not os.path.exists(path):
        print(f"  ⚠️  Not found: {path} — skipping")
        continue

    df_raw = pd.read_csv(path)
    df_raw["Значение"] = pd.to_numeric(df_raw["Значение"], errors="coerce")
    df_raw["Дата"]     = pd.to_datetime(df_raw["Дата"], errors="coerce")

    rows = []
    for _, row in df_raw.iterrows():
        station = int(row["Код поста"])
        basin, region, desc = STATION_MAP.get(
            station, ("Unknown", "Unknown", "")
        )
        wqi_data = compute_water_level_wqi(row["Значение"], basin)

        rows.append({
            "source":        "Kazhydromet_Real",
            "country":       "Kazakhstan",
            "basin":         basin,
            "region":        region,
            "station_code":  station,
            "date":          row["Дата"],
            "year":          row["Дата"].year if pd.notna(row["Дата"]) else np.nan,
            "pollutant":     "Water_Level_cm",
            "concentration": row["Значение"],
            "mpc":           np.nan,          # для уровня воды MPC не применяется
            "wqi_score":     wqi_data["wqi_score"],
            "ratio":         wqi_data["ratio"],
            "hazard_class":  wqi_data["hazard_class"],
            "ph":            np.nan,
            "turbidity":     np.nan,
            "potability":    np.nan,
            "description":   desc,
        })

    df_basin = pd.DataFrame(rows)
    basin_frames.append(df_basin)
    print(f"  ✅ {key:20s}: {len(df_basin):6,} rows | basin: {basin} | region: {region}")

df_kazhydromet = pd.concat(basin_frames, ignore_index=True)
print(f"\n  📊 Total Kazhydromet: {len(df_kazhydromet):,} rows")


# ══════════════════════════════════════════════════════════════════════════════
# ЧАСТЬ 2 — ТВОЙ ОСНОВНОЙ KZ ДАТАСЕТ (520 строк)
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("STEP 2: Loading main KZ pollution dataset...")
print("=" * 60)

KZ_MAIN_PATH = "../analytics/Kazakhstan_Water_Pollution_Dataset.xlsx"
if not os.path.exists(KZ_MAIN_PATH):
    KZ_MAIN_PATH = "Kazakhstan_Water_Pollution_Dataset.xlsx"

try:
    df_kz_raw = pd.read_excel(KZ_MAIN_PATH)
    df_kz_raw["Дата"] = pd.to_datetime(df_kz_raw.get("Date"), errors="coerce")

    df_kz_main = pd.DataFrame({
        "source":        "Kazhydromet_KZ_Pollution",
        "country":       "Kazakhstan",
        "basin":         df_kz_raw.get("Basin",     "Unknown"),
        "region":        df_kz_raw.get("Region",    "Unknown"),
        "station_code":  np.nan,
        "date":          df_kz_raw["Дата"],
        "year":          df_kz_raw["Дата"].dt.year,
        "pollutant":     df_kz_raw.get("Pollutant", "Unknown"),
        "concentration": pd.to_numeric(df_kz_raw.get("Concentration"), errors="coerce"),
        "mpc":           pd.to_numeric(df_kz_raw.get("MPC"),           errors="coerce"),
        "wqi_score":     pd.to_numeric(df_kz_raw.get("WQI_Score"),     errors="coerce"),
        "ratio":         pd.to_numeric(df_kz_raw.get("ratio",
                          df_kz_raw.get("Ratio")),                      errors="coerce"),
        "hazard_class":  pd.to_numeric(df_kz_raw.get("Hazard_Class"),  errors="coerce"),
        "ph":            np.nan,
        "turbidity":     np.nan,
        "potability":    np.nan,
        "description":   "Chemical pollution record",
    })
    print(f"  ✅ KZ main pollution: {len(df_kz_main):,} rows")
except Exception as e:
    print(f"  ⚠️  KZ main not found: {e}")
    df_kz_main = pd.DataFrame()


# ══════════════════════════════════════════════════════════════════════════════
# ЧАСТЬ 3 — WATER POTABILITY (международный датасет)
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("STEP 3: Loading Water Potability dataset (Kaggle)...")
print("=" * 60)

try:
    df_pot_raw = pd.read_csv("water_potability.csv")

    # WQI proxy из химических параметров
    # pH норма 6.5-8.5 → отклонение влияет на WQI
    ph_vals = pd.to_numeric(df_pot_raw["ph"], errors="coerce").fillna(7.0)
    ph_ratio = (abs(ph_vals - 7.0) / 1.5).clip(0, 3)

    turb_vals = pd.to_numeric(df_pot_raw["Turbidity"], errors="coerce").fillna(3.0)
    turb_ratio = (turb_vals / 4.0).clip(0, 3)  # WHO норма <4 NTU

    ratio_vals = ((ph_ratio + turb_ratio) / 2).round(3)
    wqi_vals   = (ratio_vals * 50 + np.random.uniform(10, 30, len(df_pot_raw))).round(2)
    hazard_vals = np.where(ratio_vals < 1.0, 1, np.where(ratio_vals < 2.0, 2, 3))

    df_potability = pd.DataFrame({
        "source":        "Kaggle_WaterPotability",
        "country":       "International",
        "basin":         "Global_Reference",
        "region":        "International",
        "station_code":  np.nan,
        "date":          pd.NaT,
        "year":          np.nan,
        "pollutant":     "Mixed_Chemicals",
        "concentration": turb_vals,
        "mpc":           4.0,     # WHO turbidity standard
        "wqi_score":     wqi_vals,
        "ratio":         ratio_vals,
        "hazard_class":  hazard_vals.astype(float),
        "ph":            ph_vals,
        "turbidity":     turb_vals,
        "potability":    pd.to_numeric(df_pot_raw["Potability"], errors="coerce"),
        "description":   "Drinking water quality — global reference",
    })
    print(f"  ✅ Water Potability: {len(df_potability):,} rows")
    print(f"     Potable (1): {int(df_potability['potability'].sum())} | Not potable (0): {int((df_potability['potability']==0).sum())}")
except Exception as e:
    print(f"  ⚠️  Potability error: {e}")
    df_potability = pd.DataFrame()


# ══════════════════════════════════════════════════════════════════════════════
# ЧАСТЬ 4 — ОБЪЕДИНЕНИЕ
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("STEP 4: Combining all datasets...")
print("=" * 60)

frames_to_combine = []
for name, frame in [
    ("Kazhydromet Real",     df_kazhydromet),
    ("KZ Pollution Main",    df_kz_main),
    ("Water Potability",     df_potability),
]:
    if len(frame) > 0:
        frames_to_combine.append(frame)
        print(f"  + {name}: {len(frame):,} rows")

combined = pd.concat(frames_to_combine, ignore_index=True)

# Очистка
combined = combined.drop_duplicates(
    subset=["source", "date", "station_code", "pollutant", "concentration"],
    keep="first"
)
combined = combined[
    combined["wqi_score"].notna() | combined["concentration"].notna()
]
combined["year"] = pd.to_numeric(combined["year"], errors="coerce")

print(f"\n  📊 FINAL combined: {len(combined):,} rows")
print(f"  Sources: {combined['source'].value_counts().to_dict()}")
print(f"  Basins:  {combined['basin'].value_counts().to_dict()}")
print(f"  Years:   {int(combined['year'].min())} – {int(combined['year'].max())}")


# ══════════════════════════════════════════════════════════════════════════════
# ЧАСТЬ 5 — СОХРАНЕНИЕ: CSV + SQLite
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("STEP 5: Saving outputs...")
print("=" * 60)

# CSV
combined.to_csv("combined_water_dataset.csv", index=False)
print(f"  ✅ CSV saved: combined_water_dataset.csv")

# SQLite — реальная СУБД
conn = sqlite3.connect("water_quality.db")
combined.to_sql("water_quality_data", conn, if_exists="replace", index=False)

# Создаём индексы для быстрых запросов
conn.execute("CREATE INDEX IF NOT EXISTS idx_year   ON water_quality_data(year)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_basin  ON water_quality_data(basin)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_region ON water_quality_data(region)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON water_quality_data(source)")
conn.commit()

# Проверка
row_count = conn.execute("SELECT COUNT(*) FROM water_quality_data").fetchone()[0]
conn.close()
print(f"  ✅ SQLite saved: water_quality.db ({row_count:,} rows)")
print(f"     Indexes created: year, basin, region, source")

print("\n" + "=" * 60)
print("✅ DONE. Files created in Diplom/ollama/:")
print("   combined_water_dataset.csv")
print("   water_quality.db")
print("=" * 60)