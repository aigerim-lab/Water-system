from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Kazakhstan Water Quality Dashboard",
    page_icon="💧",
    layout="wide",
)

DATA_PATH = Path("db/Kazakhstan_Water_Pollution_Dataset.csv")

# Approximate polygons to keep the choropleth fully local/offline.
REGION_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "id": "VKO",
            "properties": {"name": "VKO"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[80, 47], [86, 47], [86, 51], [80, 51], [80, 47]]],
            },
        },
        {
            "type": "Feature",
            "id": "Karaganda",
            "properties": {"name": "Karaganda"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[67, 46], [76, 46], [76, 50], [67, 50], [67, 46]]],
            },
        },
        {
            "type": "Feature",
            "id": "Kostanay",
            "properties": {"name": "Kostanay"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[62, 51], [68, 51], [68, 54], [62, 54], [62, 51]]],
            },
        },
        {
            "type": "Feature",
            "id": "Akmoal",
            "properties": {"name": "Akmoal"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[67, 50], [73, 50], [73, 54], [67, 54], [67, 50]]],
            },
        },
        {
            "type": "Feature",
            "id": "Almaty",
            "properties": {"name": "Almaty"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[75, 43], [82, 43], [82, 46], [75, 46], [75, 43]]],
            },
        },
        {
            "type": "Feature",
            "id": "Zhambyl",
            "properties": {"name": "Zhambyl"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[69, 42], [75, 42], [75, 45], [69, 45], [69, 42]]],
            },
        },
        {
            "type": "Feature",
            "id": "Kyzylorda",
            "properties": {"name": "Kyzylorda"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[60, 43], [68, 43], [68, 46], [60, 46], [60, 43]]],
            },
        },
        {
            "type": "Feature",
            "id": "Atyrau",
            "properties": {"name": "Atyrau"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[50, 45], [56, 45], [56, 49], [50, 49], [50, 45]]],
            },
        },
    ],
}


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Year"] = df["Date"].dt.year
    df["Ratio"] = np.where(df["MPC"] > 0, df["Concentration"] / df["MPC"], np.nan)
    return df.dropna(subset=["Date", "Year"])


def fit_linear_regression(year_series: pd.Series, value_series: pd.Series) -> Tuple[np.ndarray, np.ndarray]:
    x = year_series.astype(float).to_numpy()
    y = value_series.astype(float).to_numpy()
    coeffs = np.polyfit(x, y, 1)
    trend = np.polyval(coeffs, x)
    return coeffs, trend


def build_kpi(df: pd.DataFrame) -> Dict[str, float]:
    return {
        "records": float(len(df)),
        "mean_wqi": float(df["WQI_Score"].mean()),
        "mean_ratio": float(df["Ratio"].mean()),
        "high_risk_share": float((df["Ratio"] > 2).mean() * 100),
    }


def figure_to_png_bytes(fig: go.Figure) -> BytesIO | None:
    try:
        png_bytes = fig.to_image(format="png", width=1400, height=800, scale=2)
        return BytesIO(png_bytes)
    except Exception:
        return None


def apply_theme(theme: str) -> str:
    if theme == "Dark":
        st.markdown(
            """
            <style>
            .stApp {
                background-color: #0e1117;
                color: #e6edf3;
            }
            [data-testid="stSidebar"] {
                background-color: #161b22;
            }
            .hero-card {
                background: linear-gradient(120deg, #1f6feb, #238636);
                color: #ffffff;
                padding: 1rem 1.2rem;
                border-radius: 12px;
                margin-bottom: 1rem;
            }
            .footer-muted {
                color: #8b949e;
                font-size: 0.9rem;
                text-align: center;
                padding-bottom: 0.5rem;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        return "plotly_dark"

    st.markdown(
        """
        <style>
        .hero-card {
            background: linear-gradient(120deg, #1f77b4, #2ca02c);
            color: #ffffff;
            padding: 1rem 1.2rem;
            border-radius: 12px;
            margin-bottom: 1rem;
        }
        .footer-muted {
            color: #6b7280;
            font-size: 0.9rem;
            text-align: center;
            padding-bottom: 0.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    return "plotly_white"


def main() -> None:
    with st.sidebar:
        st.header("Display Settings")
        theme_mode = st.radio("Theme", ["Light", "Dark"], index=0, horizontal=True)
    plot_template = apply_theme(theme_mode)

    st.markdown(
        """
        <div class="hero-card">
            <h2 style="margin:0;">💧 Kazakhstan Water Quality Dashboard</h2>
            <p style="margin:0.3rem 0 0 0;">
                Interactive analytics platform with trends, regional comparison, and baseline ML prediction.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not DATA_PATH.exists():
        st.error(f"Dataset not found: {DATA_PATH}")
        return

    df = load_data()

    with st.sidebar:
        st.header("Filters")
        selected_regions = st.multiselect(
            "Region",
            options=sorted(df["Region"].dropna().unique()),
            default=sorted(df["Region"].dropna().unique()),
        )
        selected_years = st.multiselect(
            "Year",
            options=sorted(df["Year"].dropna().unique()),
            default=sorted(df["Year"].dropna().unique()),
        )
        selected_indicators = st.multiselect(
            "Indicator (Pollutant)",
            options=sorted(df["Pollutant"].dropna().unique()),
            default=sorted(df["Pollutant"].dropna().unique()),
        )

    filtered_df = df[
        df["Region"].isin(selected_regions)
        & df["Year"].isin(selected_years)
        & df["Pollutant"].isin(selected_indicators)
    ].copy()

    if filtered_df.empty:
        st.warning("No data for selected filters. Please widen your selection.")
        return

    kpi = build_kpi(filtered_df)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Records", f"{int(kpi['records'])}")
    c2.metric("Mean WQI", f"{kpi['mean_wqi']:.2f}")
    c3.metric("Mean Ratio", f"{kpi['mean_ratio']:.2f}")
    c4.metric("High-Risk Share", f"{kpi['high_risk_share']:.1f}%")

    st.markdown("### Regional Choropleth (Kazakhstan)")
    regional_map = (
        filtered_df.groupby("Region", as_index=False)["WQI_Score"]
        .mean()
        .rename(columns={"WQI_Score": "Mean_WQI"})
    )
    fig_map = px.choropleth(
        regional_map,
        geojson=REGION_GEOJSON,
        locations="Region",
        featureidkey="id",
        color="Mean_WQI",
        color_continuous_scale="YlOrRd",
        title="Average WQI by Region",
    )
    fig_map.update_geos(fitbounds="locations", visible=False)
    fig_map.update_layout(margin={"l": 0, "r": 0, "t": 50, "b": 0})
    fig_map.update_layout(template=plot_template)
    st.plotly_chart(fig_map, use_container_width=True)

    left, right = st.columns(2)

    with left:
        st.markdown("### Line Chart: WQI Trend")
        trend = filtered_df.groupby("Year", as_index=False)["WQI_Score"].mean()
        fig_line = px.line(
            trend,
            x="Year",
            y="WQI_Score",
            markers=True,
            title="Average WQI Over Time",
            template=plot_template,
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with right:
        st.markdown("### Bar Chart: Regions Comparison")
        region_bar = filtered_df.groupby("Region", as_index=False)["WQI_Score"].mean()
        region_bar = region_bar.sort_values("WQI_Score", ascending=False)
        fig_bar = px.bar(
            region_bar,
            x="Region",
            y="WQI_Score",
            color="WQI_Score",
            color_continuous_scale="Blues",
            title="Average WQI by Region",
            template=plot_template,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("### Prediction Chart (Linear Regression)")
    pred_target = st.radio(
        "Prediction target",
        options=["WQI_Score", "Concentration"],
        horizontal=True,
    )
    pred_data = filtered_df.groupby("Year", as_index=False)[pred_target].mean().dropna()

    if len(pred_data) >= 2:
        coeffs, trend_fit = fit_linear_regression(pred_data["Year"], pred_data[pred_target])
        next_year = int(pred_data["Year"].max()) + 1
        next_value = float(np.polyval(coeffs, next_year))

        fig_pred = go.Figure()
        fig_pred.add_trace(
            go.Scatter(
                x=pred_data["Year"],
                y=pred_data[pred_target],
                mode="lines+markers",
                name="Actual",
            )
        )
        fig_pred.add_trace(
            go.Scatter(
                x=pred_data["Year"],
                y=trend_fit,
                mode="lines",
                name="Regression line",
                line={"dash": "dash"},
            )
        )
        fig_pred.add_trace(
            go.Scatter(
                x=[next_year],
                y=[next_value],
                mode="markers+text",
                text=[f"Forecast {next_year}"],
                textposition="top center",
                marker={"size": 12, "color": "red"},
                name="Forecast",
            )
        )
        fig_pred.update_layout(
            title=f"Linear Regression Forecast for {pred_target}",
            xaxis_title="Year",
            yaxis_title=pred_target,
            template=plot_template,
        )
        st.plotly_chart(fig_pred, use_container_width=True)
    else:
        fig_pred = go.Figure()
        st.info("Not enough yearly points for linear regression prediction.")

    st.markdown("### Export")
    csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered data as CSV",
        data=csv_bytes,
        file_name="filtered_water_quality_data.csv",
        mime="text/csv",
    )

    export_options = {
        "map": fig_map,
        "trend": fig_line,
        "regions": fig_bar,
        "prediction": fig_pred,
    }
    export_chart = st.selectbox("Choose chart to export as PNG", list(export_options.keys()))
    png_file = figure_to_png_bytes(export_options[export_chart])
    if png_file is not None:
        st.download_button(
            "Download chart as PNG",
            data=png_file,
            file_name=f"{export_chart}_chart.png",
            mime="image/png",
        )
    else:
        st.warning("PNG export requires 'kaleido'. Run: pip install kaleido")

    st.markdown("---")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(f'<div class="footer-muted">Last updated: {now_str}</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
