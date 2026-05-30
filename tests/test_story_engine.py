"""Tests for environmental storytelling engine."""

from __future__ import annotations

import pandas as pd

from analytics.story_engine import generate_stories


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame({
        "Region": ["Almaty", "VKO"],
        "Basin": ["Balkash-Alakol", "Ertis"],
        "Year": [2020, 2021],
        "Pollutant": ["Nitrates", "Copper"],
        "Concentration": [10.0, 0.002],
        "MPC": [45.0, 0.001],
        "WQI_Score": [11.1, 100.0],
        "Ratio": [0.22, 2.0],
        "data_source": ["observed", "reconstructed"],
    })


def test_generate_stories_has_national_status():
    stories = generate_stories(_sample_df(), lang="en")
    assert stories["national_status"]
    assert stories["pollution_story"]
    assert "Almaty" in stories["region_stories"] or "VKO" in stories["region_stories"]
