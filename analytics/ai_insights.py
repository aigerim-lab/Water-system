"""
Rule-based natural language insight generator.

Analyses the current filtered dataset and produces 3–5 plain-English sentences.
No external API — fully reproducible and testable.

Disclaimer: outputs are algorithmically generated from the filtered data.
"""

from __future__ import annotations

import pandas as pd

DISCLAIMER = (
    "These insights are algorithmically generated from the currently filtered dataset. "
    "They do not constitute regulatory advice."
)


def generate_insights(df: pd.DataFrame) -> list[str]:
    """
    Generate rule-based insights from filtered water quality data.

    Args:
        df: Filtered dashboard DataFrame with Region, Pollutant, Ratio, WQI_Score, Year.

    Returns:
        List of insight sentences plus a disclaimer.
    """
    if df.empty:
        return ["No data available for the current filter selection.", DISCLAIMER]

    insights: list[str] = []
    n = len(df)

    # Highest-risk region by mean ratio
    if "Region" in df.columns and "Ratio" in df.columns:
        regional = df.groupby("Region")["Ratio"].mean().sort_values(ascending=False)
        if not regional.empty:
            top_region = regional.index[0]
            top_ratio = regional.iloc[0]
            insights.append(
                f"The highest-risk region in the current view is **{top_region}** "
                f"(mean pollution ratio {top_ratio:.2f}, n={n:,} records)."
            )

    # Most dangerous pollutant
    if "Pollutant" in df.columns and "Ratio" in df.columns:
        chem = df[~df["Pollutant"].isin(["Water_Level_cm", "Mixed_Chemicals"])]
        if not chem.empty:
            by_poll = chem.groupby("Pollutant")["Ratio"].mean().sort_values(ascending=False)
            worst = by_poll.index[0]
            worst_ratio = by_poll.iloc[0]
            insights.append(
                f"**{worst}** shows the highest mean pollution ratio ({worst_ratio:.2f}) "
                f"among chemical indicators in the filtered data."
            )

    # Trend direction (yearly mean WQI)
    if "Year" in df.columns and "WQI_Score" in df.columns:
        yearly = df.groupby("Year")["WQI_Score"].mean().dropna().sort_index()
        if len(yearly) >= 2:
            delta = yearly.iloc[-1] - yearly.iloc[0]
            direction = "deteriorating" if delta > 0 else "improving"
            insights.append(
                f"Water quality trend is **{direction}**: mean WQI changed by "
                f"{delta:+.1f} from {int(yearly.index[0])} to {int(yearly.index[-1])}."
            )

    # High-risk share
    if "Ratio" in df.columns:
        high_share = (df["Ratio"] >= 2.0).mean() * 100
        if high_share > 30:
            insights.append(
                f"**{high_share:.1f}%** of records exceed 2× MPC (high-risk threshold). "
                "Priority monitoring is recommended for affected basins."
            )
        elif high_share < 10:
            insights.append(
                f"Only **{high_share:.1f}%** of records exceed 2× MPC — "
                "overall pollution levels remain mostly within moderate bounds."
            )

    # Policy recommendation
    if "data_source" in df.columns:
        sources = df["data_source"].value_counts(normalize=True)
        if sources.get("reconstructed", 0) > 0.5:
            insights.append(
                "Policy note: a majority of records are statistically reconstructed; "
                "expand direct field sampling before regulatory decisions."
            )
        elif sources.get("observed", 0) > 0.5:
            insights.append(
                "Policy note: observed Kazhydromet data dominates this view — "
                "suitable for hydrological basin management decisions."
            )

    if len(insights) < 3:
        mean_wqi = df["WQI_Score"].mean() if "WQI_Score" in df.columns else float("nan")
        insights.append(f"Mean WQI in current filter: **{mean_wqi:.1f}** (n={n:,}).")

    insights.append(DISCLAIMER)
    return insights
