"""Tests for rule-based AI insights."""

from __future__ import annotations

import pandas as pd

from analytics.ai_insights import DISCLAIMER, generate_insights


def test_empty_dataframe_returns_disclaimer():
    insights = generate_insights(pd.DataFrame())
    assert len(insights) >= 1
    assert DISCLAIMER in insights[-1]


def test_generates_region_insight():
    df = pd.DataFrame(
        {
            "Region": ["Almaty", "Almaty", "VKO"],
            "Pollutant": ["Nitrates", "Copper", "Nitrates"],
            "Ratio": [2.5, 1.8, 0.5],
            "WQI_Score": [120, 90, 25],
            "Year": [2023, 2023, 2023],
            "data_source": ["reconstructed"] * 3,
        }
    )
    insights = generate_insights(df)
    assert any("Almaty" in i for i in insights)
    assert DISCLAIMER in insights[-1]
