"""
Dashboard business logic shared by FastAPI backend (and optionally Streamlit).

Presentation layers (Streamlit app.py, React frontend) call this service only —
no duplicate analytics logic in the UI.
"""

from __future__ import annotations

import json
from io import StringIO
from typing import Any, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from analytics.ai_insights import generate_insights
from analytics.ml_engine import (
    comparison_df_from_records,
    prepare_yearly_series,
    train_and_compare,
)
from analytics.shap_analysis import compute_shap_values
from config.logging_config import get_logger
from config.settings import (
    DATASET_BANNER,
    DATA_PATH,
    GEOJSON_PATH,
    LIMITATIONS,
    ML_DISCLAIMER,
    MODEL_COLORS,
    REGION_NAME_MAP,
    TREE_MODEL_NAMES,
    WHY_NOT_DEEP_LEARNING,
)
from data.loader import data_quality_summary, load_enriched
from data.validator import DataValidator
from visualization.charts import build_pollutant_region_heatmap, build_yoy_wqi_delta

logger = get_logger(__name__)

SOURCE_LABELS = {
    "observed": "Observed (Kazhydromet)",
    "reconstructed": "Reconstructed (chemical)",
    "reference": "Reference (international)",
}


class DashboardService:
    """Core dashboard operations for API and optional UI adapters."""

    def __init__(self) -> None:
        self._df: Optional[pd.DataFrame] = None
        self._geojson: Optional[dict] = None

    def load_dataset(self) -> pd.DataFrame:
        """Load and validate master dataset (cached in memory)."""
        if self._df is None:
            df = load_enriched()
            DataValidator(strict=False).validate(df)
            self._df = df
            logger.info("DashboardService loaded %d rows", len(df))
        return self._df.copy()

    def load_geojson(self) -> dict:
        """Load Kazakhstan GeoJSON with region_key mapping."""
        if self._geojson is None:
            with open(GEOJSON_PATH, encoding="utf-8") as fh:
                raw = json.load(fh)
            rev = {v.lower(): k for k, v in REGION_NAME_MAP.items()}
            for feat in raw["features"]:
                props = feat.setdefault("properties", {})
                raw_name = props.get("name", "")
                region_key = rev.get(raw_name.lower(), raw_name)
                props["region_key"] = region_key
                feat["id"] = region_key
            self._geojson = raw
        return self._geojson

    def apply_filters(
        self,
        df: pd.DataFrame,
        sources: Optional[list[str]] = None,
        regions: Optional[list[str]] = None,
        years: Optional[list[int]] = None,
        pollutants: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """Filter dataframe by sidebar criteria."""
        out = df.copy()
        if sources and "data_source" in out.columns:
            out = out[out["data_source"].isin(sources)]
        if regions:
            out = out[out["Region"].isin(regions)]
        if years:
            out = out[out["Year"].isin(years)]
        if pollutants:
            out = out[out["Pollutant"].isin(pollutants)]
        return out

    def filter_options(self, df: pd.DataFrame, sources: Optional[list[str]] = None) -> dict:
        """Return available filter values after optional source pre-filter."""
        scoped = df.copy()
        if sources and "data_source" in scoped.columns:
            scoped = scoped[scoped["data_source"].isin(sources)]
        return {
            "sources": sorted(df["data_source"].dropna().unique().tolist()) if "data_source" in df.columns else [],
            "regions": sorted(scoped["Region"].dropna().unique().tolist()),
            "years": [int(y) for y in sorted(scoped["Year"].dropna().unique())],
            "pollutants": sorted(scoped["Pollutant"].dropna().unique().tolist()),
            "source_labels": SOURCE_LABELS,
        }

    def meta(self) -> dict:
        """Static dashboard metadata for frontend."""
        return {
            "banner": DATASET_BANNER,
            "limitations": LIMITATIONS,
            "ml_disclaimer": ML_DISCLAIMER,
            "why_not_deep_learning": WHY_NOT_DEEP_LEARNING,
            "dataset_path": str(DATA_PATH),
            "dataset_exists": DATA_PATH.exists(),
        }

    def kpi(self, df: pd.DataFrame) -> dict:
        return {
            "records": int(len(df)),
            "mean_wqi": round(float(df["WQI_Score"].mean()), 2),
            "mean_ratio": round(float(df["Ratio"].mean()), 2),
            "high_risk_share": round(float((df["Ratio"] > 2).mean() * 100), 1),
        }

    def data_quality(self, df: pd.DataFrame) -> dict:
        return data_quality_summary(df)

    def risk_alerts(self, df: pd.DataFrame) -> dict:
        high = df[df["Ratio"] > 2]
        moderate = df[(df["Ratio"] >= 1) & (df["Ratio"] <= 2)]
        top = (
            df.groupby("Region", as_index=False)
            .agg(
                Mean_Ratio=("Ratio", "mean"),
                High_Risk_Records=("Ratio", lambda x: int((x > 2).sum())),
                Total_Records=("Ratio", "size"),
                Mean_WQI=("WQI_Score", "mean"),
            )
            .sort_values(["High_Risk_Records", "Mean_Ratio"], ascending=[False, False])
        )
        top["High_Risk_Share_%"] = (top["High_Risk_Records"] / top["Total_Records"] * 100).round(1)
        return {
            "high_risk_count": int(len(high)),
            "high_risk_pct": round(len(high) / len(df) * 100, 1) if len(df) else 0,
            "moderate_risk_count": int(len(moderate)),
            "moderate_risk_pct": round(len(moderate) / len(df) * 100, 1) if len(df) else 0,
            "top_regions": top.head(8).to_dict(orient="records"),
        }

    def insights(self, df: pd.DataFrame) -> list[str]:
        return generate_insights(df)

    def compare(
        self,
        df: pd.DataFrame,
        region_a: str,
        year_a: int,
        region_b: str,
        year_b: int,
    ) -> dict:
        a_df = df[(df["Region"] == region_a) & (df["Year"] == year_a)]
        b_df = df[(df["Region"] == region_b) & (df["Year"] == year_b)]
        if a_df.empty or b_df.empty:
            return {"ok": False, "message": "No data for selected region-period pairs."}
        a_wqi = float(a_df["WQI_Score"].mean())
        b_wqi = float(b_df["WQI_Score"].mean())
        a_ratio = float(a_df["Ratio"].mean())
        b_ratio = float(b_df["Ratio"].mean())
        a_high = float((a_df["Ratio"] > 2).mean() * 100)
        b_high = float((b_df["Ratio"] > 2).mean() * 100)
        return {
            "ok": True,
            "wqi_delta": round(b_wqi - a_wqi, 2),
            "ratio_delta": round(b_ratio - a_ratio, 2),
            "high_risk_delta_pp": round(b_high - a_high, 1),
            "a": {"wqi": round(a_wqi, 2), "ratio": round(a_ratio, 2), "high_risk_pct": round(a_high, 1)},
            "b": {"wqi": round(b_wqi, 2), "ratio": round(b_ratio, 2), "high_risk_pct": round(b_high, 1)},
        }

    def ml_forecast(self, df: pd.DataFrame, target: str = "WQI_Score") -> dict:
        pred_data = prepare_yearly_series(df, target)
        if len(pred_data) < 2:
            return {"ok": False, "message": "Need at least 2 yearly points for ML."}
        years = pred_data["Year"].astype(int).tolist()
        y = pred_data[target].tolist()
        forecast_year = int(max(years)) + 1
        results = train_and_compare(np.array(years, dtype=float), np.array(y), forecast_year)
        records = [
            {
                "name": r.name,
                "yhat": r.yhat.tolist(),
                "pred_next": r.pred_next,
                "insample": r.insample,
                "cv": r.cv,
                "n_samples": r.n_samples,
                "overfitting_warning": r.overfitting_warning,
            }
            for r in results
        ]
        shap_data: dict[str, list] = {}
        X = np.array(years, dtype=float).reshape(-1, 1)
        live_map = {r.name: r for r in results}
        for name in TREE_MODEL_NAMES:
            if name not in live_map:
                continue
            shap_df = compute_shap_values(live_map[name].model, name, X, feature_names=["Year"])
            if shap_df is not None:
                shap_data[name] = shap_df.to_dict(orient="records")
        cmp_df = comparison_df_from_records(records, forecast_year)
        return {
            "ok": True,
            "target": target,
            "years": years,
            "actual": y,
            "forecast_year": forecast_year,
            "models": records,
            "comparison_table": cmp_df.to_dict(orient="records"),
            "colors": MODEL_COLORS,
            "shap": shap_data,
            "any_overfitting": any(r["overfitting_warning"] for r in records),
        }

    def charts(self, df: pd.DataFrame, template: str = "plotly_white") -> dict[str, Any]:
        """Return Plotly figure JSON for all dashboard charts."""
        regional_map = (
            df.groupby("Region", as_index=False)["WQI_Score"].mean().rename(columns={"WQI_Score": "Mean_WQI"})
        )
        kz_geojson = self.load_geojson()
        fig_map = px.choropleth_mapbox(
            regional_map,
            geojson=kz_geojson,
            locations="Region",
            featureidkey="id",
            color="Mean_WQI",
            color_continuous_scale="YlOrRd",
            range_color=(
                regional_map["Mean_WQI"].min() * 0.95,
                regional_map["Mean_WQI"].max() * 1.05,
            ),
            mapbox_style="carto-positron",
            zoom=3.8,
            center={"lat": 48.0, "lon": 66.0},
            opacity=0.75,
            hover_name="Region",
            title=f"Average WQI by Region (n={len(df):,})",
            labels={"Mean_WQI": "WQI Score"},
        )
        fig_map.update_layout(margin={"l": 0, "r": 0, "t": 50, "b": 0}, template=template)

        trend = df.groupby("Year", as_index=False)["WQI_Score"].mean()
        fig_line = px.line(
            trend, x="Year", y="WQI_Score", markers=True,
            title=f"Average WQI Over Time (n={len(df):,})", template=template,
        )
        fig_line.update_layout(xaxis_title="Year", yaxis_title="WQI Score")

        region_bar = df.groupby("Region", as_index=False)["WQI_Score"].mean().sort_values("WQI_Score", ascending=False)
        fig_bar = px.bar(
            region_bar, x="Region", y="WQI_Score", color="WQI_Score",
            color_continuous_scale="Blues",
            title=f"Average WQI by Region (n={len(df):,})", template=template,
        )

        fig_heatmap = build_pollutant_region_heatmap(df, template=template, n_records=len(df))
        fig_yoy = build_yoy_wqi_delta(df, template=template)

        return {
            "map": json.loads(fig_map.to_json()),
            "trend": json.loads(fig_line.to_json()),
            "regions": json.loads(fig_bar.to_json()),
            "heatmap": json.loads(fig_heatmap.to_json()),
            "yoy_delta": json.loads(fig_yoy.to_json()),
        }

    def export_csv(self, df: pd.DataFrame) -> str:
        buf = StringIO()
        df.to_csv(buf, index=False)
        return buf.getvalue()


dashboard_service = DashboardService()
