"""Smoke tests for ML engine."""

from __future__ import annotations

import numpy as np

from analytics.ml_engine import prepare_yearly_series, train_and_compare


def test_models_train_on_synthetic_series():
    years = np.array([2020, 2021, 2022, 2023, 2024], dtype=float)
    y = np.array([100.0, 95.0, 90.0, 88.0, 85.0])
    results = train_and_compare(years, y, forecast_year=2025, n_cv_splits=3)
    assert len(results) >= 4
    for res in results:
        assert res.n_samples == 5
        assert 0 <= res.pred_next < 500
        assert "mape" in res.insample
        assert "mape" in res.cv


def test_prepare_yearly_series():
    import pandas as pd

    df = pd.DataFrame(
        [
            {"Year": 2020, "WQI_Score": 50.0},
            {"Year": 2020, "WQI_Score": 60.0},
            {"Year": 2021, "WQI_Score": 40.0},
        ]
    )
    series = prepare_yearly_series(df, "WQI_Score")
    assert len(series) == 2
    assert series.loc[series["Year"] == 2020, "WQI_Score"].iloc[0] == 55.0
