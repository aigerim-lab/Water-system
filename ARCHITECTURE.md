# Architecture

Technical architecture reference for AquaMonitor. Installation and usage: [README.md](README.md).

## Layer diagram

```
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND — React + Vite + Plotly  (frontend/, :5173)       │
│  Filters · Map · Charts · Forecast · Compare · Chat         │
└──────────────────────────┬──────────────────────────────────┘
                           │  REST  /api/dashboard/*
┌──────────────────────────▼──────────────────────────────────┐
│  BACKEND — FastAPI  (backend/main.py, :8001)                  │
│  backend/api/routes/dashboard.py                              │
│  backend/services/dashboard_service.py                        │
└───────────────┬──────────────────────────────┬────────────────┘
                │                              │
┌───────────────▼──────────────┐   ┌───────────▼────────────────┐
│  DATA + ANALYTICS             │   │  OLLAMA (local LLM)         │
│  data/loader.py               │   │  localhost:11434            │
│  analytics/wqi.py             │   │  analytics/ollama_client.py │
│  analytics/ml_engine.py       │   └────────────────────────────┘
│  analytics/gis_layers.py      │
│  analytics/chat_assistant.py  │
│  config/settings.py           │
│  db/kazakhstan_water_master   │
└──────────────────────────────┘
```

## Environmental Intelligence Analyst flow

```
User Question
    ↓
Current Filters (region, basin, year, pollutant, source)
    ↓
AquaMonitor Analytics Context
    WQI · trends · hotspots · basin stats · forecast · risk alerts
    ↓
Ollama LLM  (analytics/ollama_client.py)
    ↓
Environmental Explanation  (analytics/chat_assistant.py)
    ↓
POST /api/dashboard/chat  →  React ChatPanel
```

**Fallback:** If Ollama is unreachable, the response includes *"Ollama model unavailable"* and rule-based summaries built from the same analytics context.

**Status:** `GET /api/dashboard/analyst/status`

## API surface

All dashboard routes are prefixed with `/api/dashboard`:

| Route | Purpose |
|-------|---------|
| `GET /meta` | Dataset metadata, limitations, row counts |
| `GET /geojson` | Kazakhstan region boundaries |
| `GET /gis/static` | Static GIS layer definitions |
| `POST /gis` | Filter-scoped GIS payloads |
| `POST /filter-options` | Valid filter values for current selection |
| `POST /summary` | KPIs, insights, national status |
| `POST /charts` | Plotly-compatible chart data |
| `POST /ml` | ML forecast results (8 models) |
| `POST /compare` | Region/period comparison |
| `GET /analyst/status` | Ollama connectivity and model |
| `POST /chat` | Environmental analyst messages |
| `POST /export/csv` | Filtered dataset export |

Health check: `GET /api/health`

## Data pipeline

```
ollama/*.csv  (Kazhydromet basins + potability reference)
        +
db/Kazakhstan_Water_Pollution_Dataset.csv  (legacy chemical)
        ↓
data/build_dataset.py
        ↓
db/kazakhstan_water_master.csv
        ↓
data/loader.py  →  dashboard_service  →  analytics modules
```

## Module responsibilities

| Directory | Role |
|-----------|------|
| `frontend/` | SPA, i18n (KK/RU/EN), map, charts, chat UI |
| `backend/` | HTTP API, Pydantic schemas, service orchestration |
| `analytics/` | WQI, hazard, ML, GIS, insights, chat, Ollama client |
| `config/` | MPC values, paths, hyperparameters, limitations |
| `data/` | Dataset build, load, validate; GIS GeoJSON assets |
| `visualization/` | Server-side Plotly chart builders |
| `tests/` | pytest unit and integration tests |
| `archive/` | Legacy Streamlit thesis dashboard |

## Note on `ollama/` folder

The `ollama/` directory holds **Kazhydromet raw CSV inputs** for `data/build_dataset.py` (legacy folder name). The live LLM integration runs via the Ollama HTTP API — not from files in that folder.

## Legacy Streamlit UI

`archive/streamlit_thesis_dashboard.py` is a standalone thesis prototype. It does not require the FastAPI backend and shares analytics modules with the React stack.
