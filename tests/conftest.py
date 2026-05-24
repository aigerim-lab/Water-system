"""Shared pytest fixtures."""

from __future__ import annotations

import pandas as pd
import pytest

from config.settings import WQI_SCALE_FACTOR


@pytest.fixture
def sample_pollution_row() -> dict:
    """Single chemical pollution record at exactly 1× MPC."""
    return {"Concentration": 45.0, "MPC": 45.0, "Pollutant": "Nitrates"}


@pytest.fixture
def sample_wqi_cases() -> list[dict]:
    """Reference WQI values computed manually: WQI = ratio × 50."""
    return [
        {"concentration": 0.0, "mpc": 45.0, "expected_wqi": 0.0},
        {"concentration": 45.0, "mpc": 45.0, "expected_wqi": WQI_SCALE_FACTOR},
        {"concentration": 90.0, "mpc": 45.0, "expected_wqi": 100.0},
        {"concentration": 0.0005, "mpc": 0.001, "expected_wqi": 25.0},
    ]
