"""Hazard and risk classification utilities."""

from __future__ import annotations

from typing import Optional

import pandas as pd

from config.settings import HAZARD_THRESHOLDS, POLLUTANTS


def classify_risk_level(ratio: float) -> str:
    """
    Classify pollution risk from Concentration/MPC ratio.

    Three-tier system (SanPiN-aligned):
      - Safe:     ratio < 1.0
      - Moderate: 1.0 ≤ ratio < 2.0
      - High:     ratio ≥ 2.0
    """
    if pd.isna(ratio):
        return "Unknown"
    if ratio < HAZARD_THRESHOLDS["safe_max"]:
        return "Safe"
    if ratio < HAZARD_THRESHOLDS["moderate_max"]:
        return "Moderate"
    return "High"


def classify_risk_code(ratio: float) -> int:
    """Numeric risk code: 1=Safe, 2=Moderate, 3=High, 0=Unknown."""
    level = classify_risk_level(ratio)
    return {"Safe": 1, "Moderate": 2, "High": 3}.get(level, 0)


def pollutant_hazard_class(pollutant: str) -> Optional[int]:
    """Intrinsic hazard class of the pollutant type (not ratio-based)."""
    spec = POLLUTANTS.get(pollutant)
    return spec.hazard_class if spec else None
