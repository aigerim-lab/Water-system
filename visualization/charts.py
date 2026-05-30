"""Chart builders for the water quality dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def build_pollutant_region_heatmap(
    df: pd.DataFrame,
    template: str = "plotly_white",
    n_records: int | None = None,
    labels: dict[str, str] | None = None,
) -> go.Figure:
    lbl = labels or {}
    px_l = lbl.get("pollutant", "Pollutant")
    py_l = lbl.get("region", "Region")
    pc_l = lbl.get("ratio", "Mean ratio (C/MPC)")
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
        labels=dict(x=px_l, y=py_l, color=pc_l),
        color_continuous_scale="Viridis",
        aspect="auto",
        template=template,
    )
    fig.update_layout(
        xaxis_title=px_l,
        yaxis_title=py_l,
        coloraxis_colorbar_title=pc_l,
    )
    return fig


def build_yoy_wqi_delta(
    df: pd.DataFrame,
    template: str = "plotly_white",
    labels: dict[str, str] | None = None,
) -> go.Figure:
    lbl = labels or {}
    imp = lbl.get("improving", "Improving")
    det = lbl.get("deteriorating", "Deteriorating")
    rx = lbl.get("wqi_delta", "Δ WQI (last − first year)")
    ry = lbl.get("region", "Region")
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
    delta_df["direction"] = delta_df["WQI_delta"].apply(lambda x: det if x > 0 else imp)
    fig = px.bar(
        delta_df,
        x="WQI_delta",
        y="Region",
        color="direction",
        color_discrete_map={imp: "#10B981", det: "#EF4444"},
        orientation="h",
        labels={"WQI_delta": rx, "Region": ry},
        template=template,
    )
    return fig
