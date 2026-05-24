# Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND (choose one or run both)                          │
│  • React web app     →  frontend/   (npm run dev, :5173)    │
│  • Streamlit UI      →  app.py      (legacy, preserved)     │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST /api/*
┌──────────────────────────▼──────────────────────────────────┐
│  BACKEND  FastAPI  backend/main.py  (:8000)                   │
│  backend/services/dashboard_service.py                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  DATA + ANALYTICS                                            │
│  data/  analytics/  config/  db/kazakhstan_water_master.csv │
└─────────────────────────────────────────────────────────────┘
```

## Quick start (React + API)

```bash
# Terminal 1 — Backend
cd Water-system
python3 -m pip install -r requirements.txt
python3 -m data.build_dataset
python3 -m uvicorn backend.main:app --reload --port 8000

# Terminal 2 — React frontend
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

## Streamlit (unchanged)

```bash
python3 -m streamlit run app.py
```

Open **http://localhost:8501**

## API docs

With backend running: **http://localhost:8000/docs**
