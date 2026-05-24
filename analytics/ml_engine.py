"""
Machine learning engine for temporal WQI / concentration forecasting.

Methodology:
  - Feature: Year (annual aggregate)
  - Validation: TimeSeriesSplit (respects temporal ordering)
  - Metrics: MAE, RMSE, R², MAPE (CV-averaged + in-sample for visualization)
  - random_state=42 on all stochastic estimators (config.settings.RANDOM_SEED)

Model selection rationale (thesis defence):
  - Linear Regression: only structurally overfitting-proof model on n≈5
  - Tree-based models: overfitting demonstrations and cross-validators
  - Boosting models: completeness of comparative study

Deep learning is NOT applied: n=5 annual observations is insufficient for
neural networks (minimum n≥50 for LSTM temporal models).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.linear_model import ElasticNet, LinearRegression
from sklearn.model_selection import TimeSeriesSplit
from sklearn.tree import DecisionTreeRegressor

from analytics.metrics import compute_all_metrics
from config.logging_config import get_logger
from config.settings import MODEL_HYPERPARAMS, OVERFITTING_R2_THRESHOLD, RANDOM_SEED, TREE_MODEL_NAMES

logger = get_logger(__name__)


@dataclass
class ModelResult:
    """Training and cross-validation results for one model."""

    name: str
    yhat: np.ndarray
    pred_next: float
    insample: dict[str, float]
    cv: dict[str, float]
    n_samples: int
    n_cv_folds: int
    overfitting_warning: bool
    model: Any = field(repr=False)


def _build_model_registry() -> Dict[str, Any]:
    """Instantiate all available models; skip optional deps that fail to import."""
    registry: Dict[str, Any] = {
        "Linear Regression": LinearRegression(),
        "Decision Tree": DecisionTreeRegressor(**MODEL_HYPERPARAMS["Decision Tree"]),
        "Random Forest": RandomForestRegressor(**MODEL_HYPERPARAMS["Random Forest"]),
        "Extra Trees": ExtraTreesRegressor(**MODEL_HYPERPARAMS["Extra Trees"]),
        "ElasticNet": ElasticNet(**MODEL_HYPERPARAMS["ElasticNet"]),
    }
    optional: Dict[str, Callable[[], Any]] = {
        "XGBoost": lambda: __import__("xgboost", fromlist=["XGBRegressor"]).XGBRegressor(
            **MODEL_HYPERPARAMS["XGBoost"]
        ),
        "LightGBM": lambda: __import__("lightgbm", fromlist=["LGBMRegressor"]).LGBMRegressor(
            **MODEL_HYPERPARAMS["LightGBM"]
        ),
        "CatBoost": lambda: __import__("catboost", fromlist=["CatBoostRegressor"]).CatBoostRegressor(
            **MODEL_HYPERPARAMS["CatBoost"]
        ),
    }
    for name, factory in optional.items():
        try:
            registry[name] = factory()
        except Exception as exc:
            logger.warning("Model %s unavailable: %s", name, exc)
    return registry


def _timeseries_cv_metrics(
    model: Any,
    X: np.ndarray,
    y: np.ndarray,
    n_splits: int,
) -> dict[str, float]:
    """Run TimeSeriesSplit CV and return mean MAE, RMSE, R², MAPE."""
    if len(y) < 3:
        return {"mae": float("nan"), "rmse": float("nan"), "r2": float("nan"), "mape": float("nan")}

    n_splits = min(n_splits, len(y) - 1)
    if n_splits < 2:
        return {"mae": float("nan"), "rmse": float("nan"), "r2": float("nan"), "mape": float("nan")}

    tscv = TimeSeriesSplit(n_splits=n_splits)
    fold_metrics: List[dict[str, float]] = []

    for train_idx, test_idx in tscv.split(X):
        est = clone(model)
        est.fit(X[train_idx], y[train_idx])
        y_pred = est.predict(X[test_idx])
        fold_metrics.append(compute_all_metrics(y[test_idx], y_pred))

    return {
        metric: float(np.nanmean([f[metric] for f in fold_metrics]))
        for metric in ("mae", "rmse", "r2", "mape")
    }


def prepare_yearly_series(df: pd.DataFrame, target: str) -> pd.DataFrame:
    """Aggregate filtered data to yearly mean for temporal modelling."""
    if "Year" not in df.columns:
        raise ValueError("DataFrame must contain a Year column")
    series = df.groupby("Year", as_index=False)[target].mean().dropna()
    return series.sort_values("Year").reset_index(drop=True)


def train_and_compare(
    years: np.ndarray,
    y: np.ndarray,
    forecast_year: Optional[int] = None,
    n_cv_splits: int = 3,
) -> List[ModelResult]:
    """
    Train all models, run TimeSeriesSplit CV, and produce next-year forecasts.

    Args:
        years: Sorted array of calendar years.
        y: Target values (WQI or concentration).
        forecast_year: Year to forecast; defaults to max(years) + 1.
        n_cv_splits: Number of TimeSeriesSplit folds.

    Returns:
        List of ModelResult sorted by CV MAE (best first).
    """
    years = np.asarray(years, dtype=float).reshape(-1, 1)
    y = np.asarray(y, dtype=float)
    n = len(y)
    next_year = int(forecast_year or (years.max() + 1))
    X_next = np.array([[float(next_year)]])

    results: List[ModelResult] = []
    registry = _build_model_registry()

    for name, model in registry.items():
        try:
            cv = _timeseries_cv_metrics(model, years, y, n_cv_splits)
            fitted = clone(model)
            fitted.fit(years, y)
            yhat = fitted.predict(years)
            pred_next = float(fitted.predict(X_next)[0])
            insample = compute_all_metrics(y, yhat)
            overfit = (
                name in TREE_MODEL_NAMES
                and insample["r2"] > OVERFITTING_R2_THRESHOLD
                and n < 10
            )
            results.append(
                ModelResult(
                    name=name,
                    yhat=yhat,
                    pred_next=pred_next,
                    insample=insample,
                    cv=cv,
                    n_samples=n,
                    n_cv_folds=min(n_cv_splits, max(n - 1, 0)),
                    overfitting_warning=overfit,
                    model=fitted,
                )
            )
            logger.info(
                "Trained %s | n=%d | CV MAE=%.3f | in-sample R²=%.3f",
                name,
                n,
                cv["mae"],
                insample["r2"],
            )
        except Exception as exc:
            logger.exception("Failed to train %s: %s", name, exc)

    results.sort(key=lambda r: r.cv["mae"] if not np.isnan(r.cv["mae"]) else float("inf"))
    return results


def results_to_comparison_df(results: List[ModelResult], forecast_year: int) -> pd.DataFrame:
    """Build ranked comparison table for dashboard display."""
    rows = []
    for rank, res in enumerate(results, start=1):
        rows.append(_comparison_row(rank, res.name, res.pred_next, res.cv, res.insample, res.overfitting_warning, forecast_year))
    return pd.DataFrame(rows)


def comparison_df_from_records(records: List[dict], forecast_year: int) -> pd.DataFrame:
    """Build comparison table from cached serializable ML records."""
    rows = []
    for rank, rec in enumerate(records, start=1):
        rows.append(
            _comparison_row(
                rank,
                rec["name"],
                rec["pred_next"],
                rec["cv"],
                rec["insample"],
                rec["overfitting_warning"],
                forecast_year,
            )
        )
    return pd.DataFrame(rows)


def _comparison_row(
    rank: int,
    name: str,
    pred_next: float,
    cv: dict,
    insample: dict,
    overfitting: bool,
    forecast_year: int,
) -> dict:
    def _fmt(val: float) -> str | float:
        return round(val, 3) if val == val else "—"

    return {
        "Rank": rank,
        "Model": name,
        f"Pred {forecast_year}": round(pred_next, 2),
        "CV MAE": _fmt(cv["mae"]),
        "CV RMSE": _fmt(cv["rmse"]),
        "CV R²": _fmt(cv["r2"]),
        "CV MAPE %": round(cv["mape"], 2) if cv["mape"] == cv["mape"] else "—",
        "In-sample R²": round(insample["r2"], 3),
        "Overfit ⚠": "Yes" if overfitting else "No",
    }
