"""Chart builders for the water quality dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def build_pollutant_region_heatmap(
    df: pd.DataFrame,
    template: str = "plotly_white",
    n_records: int | None = None,
) -> go.Figure:
    """
    Build pollutant × region heatmap of mean pollution ratio.

    Suitable for thesis defence slides. Uses Viridis (colorblind-safe).
    """
    chem_pollutants = {"Nitrates", "Copper", "Sulfates", "Zinc", "Phenols", "Oil Products"}
    subset = df[df["Pollutant"].isin(chem_pollutants)] if "Pollutant" in df.columns else df

    if subset.empty or "Region" not in subset.columns or "Ratio" not in subset.columns:
        fig = go.Figure()
        fig.update_layout(title="Pollutant × Region heatmap — no chemical data in filter")
        return fig

    pivot = (
        subset.groupby(["Region", "Pollutant"], as_index=False)["Ratio"]
        .mean()
        .pivot(index="Region", columns="Pollutant", values="Ratio")
    )
    n = n_records or len(subset)
    fig = px.imshow(
        pivot,
        labels=dict(x="Pollutant", y="Region", color="Mean ratio (C/MPC)"),
        color_continuous_scale="Viridis",
        aspect="auto",
        title=f"Mean pollution ratio by pollutant and region (n={n:,})",
        template=template,
    )
    fig.update_layout(
        xaxis_title="Pollutant",
        yaxis_title="Region",
        coloraxis_colorbar_title="Ratio (C/MPC)",
    )
    return fig


def build_yoy_wqi_delta(df: pd.DataFrame, template: str = "plotly_white") -> go.Figure:
    """Year-over-year WQI change per region (improving vs deteriorating)."""
    if df.empty or "Year" not in df.columns:
        fig = go.Figure()
        fig.update_layout(title="YoY WQI delta — insufficient data")
        return fig

    yearly = df.groupby(["Region", "Year"], as_index=False)["WQI_Score"].mean()
    if yearly.empty:
        fig = go.Figure()
        return fig

    deltas = []
    for region, grp in yearly.groupby("Region"):
        grp = grp.sort_values("Year")
        if len(grp) < 2:
            continue
        delta = grp["WQI_Score"].iloc[-1] - grp["WQI_Score"].iloc[0]
        deltas.append({"Region": region, "WQI_delta": delta})

    if not deltas:
        fig = go.Figure()
        fig.update_layout(title="YoY WQI delta — need ≥2 years per region")
        return fig

    delta_df = pd.DataFrame(deltas).sort_values("WQI_delta")
    delta_df["direction"] = delta_df["WQI_delta"].apply(
        lambda x: "Deteriorating" if x > 0 else "Improving"
    )
    fig = px.bar(
        delta_df,
        x="WQI_delta",
        y="Region",
        color="direction",
        color_discrete_map={"Improving": "#10B981", "Deteriorating": "#EF4444"},
        orientation="h",
        title="Year-over-year WQI change by region (last − first year in filter)",
        labels={"WQI_delta": "Δ WQI (last year − first year)", "Region": "Region"},
        template=template,
    )
    return fig
