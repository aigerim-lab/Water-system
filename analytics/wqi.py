"""
Water Quality Index (WQI) computation — MPC-anchored sub-indices.

Foundational references:
  - Horton, R.K. (1965). An index number system for rating water quality.
  - Brown, R.M. et al. (1970). A water quality index — critical review.

This implementation uses MPC-anchored sub-indices rather than arbitrary
weight assignment, which is more interpretable for Kazakhstan SanPiN regulatory
context: WQI_i = (C_i / MPC_i) × WQI_SCALE_FACTOR.

Interpretation:
  - WQI < 50  : concentration below MPC (safer)
  - WQI = 50  : at MPC boundary
  - WQI = 100 : at 2× MPC (moderate risk boundary)
  - WQI > 100 : high pollution risk
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from config.settings import BASIN_WATER_LEVEL_RANGES, WQI_SCALE_FACTOR


def compute_pollution_wqi(concentration: float, mpc: float) -> float:
    """
    Compute MPC-anchored WQI for a chemical pollutant record.

    Args:
        concentration: Measured concentration (mg/L).
        mpc: Maximum Permissible Concentration (SanPiN fishery-use, mg/L).

    Returns:
        WQI score. Returns NaN if mpc <= 0 or inputs are NaN.
    """
    if pd.isna(concentration) or pd.isna(mpc) or mpc <= 0:
        return float("nan")
    ratio = concentration / mpc
    return round(ratio * WQI_SCALE_FACTOR, 2)


def compute_pollution_ratio(concentration: float, mpc: float) -> float:
    """Compute pollution ratio (Concentration / MPC)."""
    if pd.isna(concentration) or pd.isna(mpc) or mpc <= 0:
        return float("nan")
    return round(concentration / mpc, 4)


def compute_water_level_ratio(value: float, basin: str) -> float:
    """
    Compute hydrological deviation ratio from basin-normal water level (cm).

    ratio = |value - mid| / span, where mid and span derive from
    Kazhydromet basin reference ranges.
    """
    if pd.isna(value):
        return float("nan")
    lo, hi = BASIN_WATER_LEVEL_RANGES.get(basin, (50, 500))
    mid = (lo + hi) / 2
    span = (hi - lo) / 2 or 1.0
    return round(abs(value - mid) / span, 4)


def compute_water_level_wqi(value: float, basin: str) -> float:
    """WQI proxy from water-level deviation (no random noise)."""
    ratio = compute_water_level_ratio(value, basin)
    if pd.isna(ratio):
        return float("nan")
    return round(ratio * WQI_SCALE_FACTOR, 2)


def compute_potability_ratio(ph: float, turbidity: float) -> float:
    """
    Reference ratio from pH and turbidity (WHO drinking-water norms).

    pH optimal = 7.0 (±1.5 tolerance); turbidity MPC = 4 NTU.
    """
    ph_val = 7.0 if pd.isna(ph) else float(ph)
    turb_val = 3.0 if pd.isna(turbidity) else float(turbidity)
    ph_ratio = min(abs(ph_val - 7.0) / 1.5, 3.0)
    turb_ratio = min(turb_val / 4.0, 3.0)
    return round((ph_ratio + turb_ratio) / 2, 4)


def compute_potability_wqi(ph: float, turbidity: float) -> float:
    """WQI for international potability reference records."""
    ratio = compute_potability_ratio(ph, turbidity)
    return round(ratio * WQI_SCALE_FACTOR, 2)


def aggregate_wqi_horton(sub_indices: pd.Series, weights: pd.Series | None = None) -> float:
    """
    Aggregate multiple sub-indices using Horton (1965) weighted mean.

    WQI = Σ(w_i × q_i) / Σ(w_i)

    Args:
        sub_indices: Per-parameter WQI sub-indices.
        weights: Optional weights; defaults to equal weights.

    Returns:
        Aggregated WQI or NaN if no valid values.
    """
    valid = sub_indices.dropna()
    if valid.empty:
        return float("nan")
    if weights is None:
        return round(float(valid.mean()), 2)
    w = weights.loc[valid.index].fillna(1.0)
    if w.sum() == 0:
        return round(float(valid.mean()), 2)
    return round(float((valid * w).sum() / w.sum()), 2)
