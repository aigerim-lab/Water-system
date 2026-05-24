"""Unit tests for MPC-anchored WQI formula correctness."""

from __future__ import annotations

import math

from analytics.hazard import classify_risk_level
from analytics.wqi import (
    compute_pollution_ratio,
    compute_pollution_wqi,
    compute_water_level_wqi,
)
from config.settings import WQI_SCALE_FACTOR


class TestPollutionWQI:
    """WQI = (Concentration / MPC) × WQI_SCALE_FACTOR."""

    def test_at_mpc_boundary(self, sample_wqi_cases):
        case = sample_wqi_cases[1]
        wqi = compute_pollution_wqi(case["concentration"], case["mpc"])
        assert wqi == WQI_SCALE_FACTOR

    def test_at_double_mpc(self, sample_wqi_cases):
        case = sample_wqi_cases[2]
        wqi = compute_pollution_wqi(case["concentration"], case["mpc"])
        assert wqi == 100.0

    def test_below_mpc(self, sample_wqi_cases):
        case = sample_wqi_cases[3]
        wqi = compute_pollution_wqi(case["concentration"], case["mpc"])
        assert wqi == 25.0

    def test_zero_concentration(self):
        assert compute_pollution_wqi(0.0, 45.0) == 0.0

    def test_nan_inputs(self):
        assert math.isnan(compute_pollution_wqi(float("nan"), 45.0))
        assert math.isnan(compute_pollution_wqi(10.0, float("nan")))
        assert math.isnan(compute_pollution_wqi(10.0, 0.0))

    def test_ratio_consistency(self):
        conc, mpc = 17.1526, 45.0
        ratio = compute_pollution_ratio(conc, mpc)
        wqi = compute_pollution_wqi(conc, mpc)
        assert abs(wqi - ratio * WQI_SCALE_FACTOR) < 0.01


class TestHazardClassification:
    def test_safe_moderate_high(self):
        assert classify_risk_level(0.5) == "Safe"
        assert classify_risk_level(1.5) == "Moderate"
        assert classify_risk_level(2.5) == "High"


class TestWaterLevelWQI:
    def test_deterministic_no_randomness(self):
        wqi1 = compute_water_level_wqi(100.0, "Ertis")
        wqi2 = compute_water_level_wqi(100.0, "Ertis")
        assert wqi1 == wqi2
