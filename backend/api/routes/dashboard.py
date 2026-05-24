"""Dashboard REST routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from backend.schemas.models import CompareRequest, FilterRequest, MLRequest
from backend.services.dashboard_service import dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _filtered(body: FilterRequest):
    df = dashboard_service.load_dataset()
    filtered = dashboard_service.apply_filters(
        df,
        sources=body.sources,
        regions=body.regions,
        years=body.years,
        pollutants=body.pollutants,
    )
    if filtered.empty:
        raise HTTPException(status_code=404, detail="No data for selected filters.")
    return filtered


@router.get("/meta")
def get_meta():
    return dashboard_service.meta()


@router.get("/geojson")
def get_geojson():
    return dashboard_service.load_geojson()


@router.post("/filter-options")
def filter_options(body: FilterRequest):
    df = dashboard_service.load_dataset()
    return dashboard_service.filter_options(df, sources=body.sources)


@router.post("/summary")
def dashboard_summary(body: FilterRequest):
    filtered = _filtered(body)
    return {
        "kpi": dashboard_service.kpi(filtered),
        "data_quality": dashboard_service.data_quality(filtered),
        "risk_alerts": dashboard_service.risk_alerts(filtered),
        "insights": dashboard_service.insights(filtered),
        "record_count": len(filtered),
    }


@router.post("/charts")
def dashboard_charts(body: FilterRequest):
    filtered = _filtered(body)
    return dashboard_service.charts(filtered)


@router.post("/ml")
def dashboard_ml(body: MLRequest):
    filtered = _filtered(body)
    return dashboard_service.ml_forecast(filtered, target=body.target)


@router.post("/compare")
def dashboard_compare(body: CompareRequest):
    df = dashboard_service.load_dataset()
    filtered = dashboard_service.apply_filters(
        df,
        sources=body.sources,
        regions=body.regions,
        years=body.years,
        pollutants=body.pollutants,
    )
    return dashboard_service.compare(
        filtered, body.region_a, body.year_a, body.region_b, body.year_b
    )


@router.post("/export/csv")
def export_csv(body: FilterRequest):
    filtered = _filtered(body)
    csv_text = dashboard_service.export_csv(filtered)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=filtered_water_quality_data.csv"},
    )
