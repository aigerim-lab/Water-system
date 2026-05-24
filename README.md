# AquaMonitor — Kazakhstan Water Quality Intelligence System

Bachelor's thesis project: monitoring, analysis, and forecasting of surface water quality in Kazakhstan using a hybrid environmental dataset (~52,600 records), MPC-anchored WQI scoring, and machine learning.

**Three-layer architecture:** React or Streamlit (presentation) → FastAPI (API) → data & analytics (business logic).

See [ARCHITECTURE.md](ARCHITECTURE.md) for a diagram and layer details.

---

## Features

| Module | Description |
|--------|-------------|
| **Overview** | KPIs, data-quality split, risk assessment, rule-based insights |
| **Maps & Charts** | Choropleth map, temporal trends, regional ranking, pollutant heatmap, YoY delta |
| **Forecast** | 8 ML models with TimeSeriesSplit CV (MAE, RMSE, R², MAPE) |
| **Compare** | Side-by-side region/period comparison with delta metrics |
| **Export** | Filtered CSV and chart PNG (Streamlit) |

**React UI:** Palantir-inspired control-center layout, full-width dashboard, EN/RU language switch (default: English).

**Streamlit UI:** Full analytical prototype preserved in `app.py` — heatmap, SHAP, AI insights, 8-model ML tab.

---

## Quick start (React + FastAPI)

### 1. Install Python dependencies

```bash
cd Water-system
python3 -m pip install -r requirements.txt
```

### 2. Build the master dataset (first run only)

Skip if `db/kazakhstan_water_master.csv` already exists.

```bash
python3 -m data.build_dataset
```

### 3. Start the backend (Terminal 1)

```bash
python3 -m uvicorn backend.main:app --reload --port 8001
```

API docs: [http://localhost:8001/docs](http://localhost:8001/docs)

> The React dev server proxies `/api` to port **8001** (see `frontend/vite.config.js`).

### 4. Start the React frontend (Terminal 2)

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

---

## Alternative: Streamlit dashboard

Standalone — does not require the FastAPI backend.

```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501)

---

## Dataset

Master file: `db/kazakhstan_water_master.csv` (~52,594 rows)

| Source | Rows (approx.) | Description |
|--------|----------------|-------------|
| `observed` | 48,798 | Kazhydromet water-level observations |
| `reconstructed` | 520 | Chemical pollution (WQI recalculated) |
| `reference` | 3,276 | Kaggle water potability (comparison only) |

**Rebuild pipeline:** merges Kazhydromet basin CSVs, chemical dataset, and reference data via `data/build_dataset.py`.

### Key columns

`Date`, `Basin`, `Region`, `Pollutant`, `Concentration`, `MPC`, `WQI_Score`, `Hazard_Class`, `data_source`, `Year`, `Ratio`

---

## Analytics

### Pollution ratio

```
Ratio = Concentration / MPC
```

### Hazard classification

| Ratio | Class |
|-------|-------|
| &lt; 1.0 | Safe |
| 1.0 – 2.0 | Moderate |
| ≥ 2.0 | High risk |

### WQI (MPC-anchored)

```
WQI = (Concentration / MPC) × 50
```

- WQI = 50 at the MPC boundary  
- WQI &lt; 50 → below MPC (safer)  
- WQI &gt; 100 → above 2× MPC  

Based on Horton (1965) / Brown et al. (1970), adapted to Kazakhstan SanPiN fishery MPC standards. See `analytics/wqi.py` and `config/settings.py`.

### Machine learning

- **Models:** Linear Regression, Decision Tree, Random Forest, Extra Trees, ElasticNet, XGBoost, LightGBM, CatBoost  
- **Validation:** `TimeSeriesSplit` cross-validation  
- **Metrics:** MAE, RMSE, R², MAPE  
- **Note:** Annual aggregation yields n≈5 points — tree/boosting models may overfit; Linear Regression is the primary interpretable model.

---

## Project structure

```
Water-system/
├── app.py                    # Streamlit dashboard (preserved)
├── backend/                  # FastAPI REST API
│   ├── main.py
│   ├── api/routes/dashboard.py
│   └── services/dashboard_service.py
├── frontend/                 # React + Vite + Plotly
│   └── src/i18n/             # EN / RU translations
├── analytics/                # WQI, hazard, ML engine, SHAP, insights
├── config/                   # MPC, thresholds, paths, limitations
├── data/                     # loader, validator, build_dataset
├── db/
│   ├── kazakhstan_water_master.csv
│   └── water_quality.db
├── visualization/            # Plotly chart builders
├── tests/                    # pytest (12 tests)
├── ollama/                   # Raw source CSVs for dataset build
├── ARCHITECTURE.md
└── Chapter4_Implementation.md
```

---

## Tests

```bash
python3 -m pytest tests/ -v
```

Covers WQI calculation, ML pipeline, and rule-based insights.

---

## System dependencies

### macOS

XGBoost / LightGBM may require OpenMP:

```bash
brew install libomp
```

Use `python3 -m pip` and `python3 -m streamlit` (not bare `pip` / `streamlit`).

### Windows / Linux

Usually no extra steps — install via `pip` as above. LightGBM, CatBoost, and SHAP degrade gracefully if unavailable.

---

## Known limitations

Documented in `config/settings.py` (L1–L6):

1. Small sample for annual ML forecasting (n≈5 years)  
2. Reconstructed chemical records where direct measurements are missing  
3. Kazhydromet water levels proxy hydrology, not chemical concentration  
4. Reference (Kaggle) data is for comparison only  
5. Tree models overfit on n&lt;10 — trust CV metrics  
6. WQI uses SanPiN MPC standards with disclosed hybrid dataset  

---

## License & attribution

- Kazakhstan map GeoJSON: `kz.json` (SimpleMaps, CC BY 4.0)  
- Kazhydromet basin data: `ollama/*.csv`  
- Diploma thesis — research use
