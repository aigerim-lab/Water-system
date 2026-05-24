"""Data validation on load."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from config.logging_config import get_logger
from config.settings import HAZARD_THRESHOLDS, POLLUTANTS

logger = get_logger(__name__)

REQUIRED_COLUMNS = {
    "Date",
    "Basin",
    "Region",
    "Pollutant",
    "Concentration",
    "WQI_Score",
}


@dataclass
class ValidationReport:
    """Structured output from DataValidator."""

    passed: bool
    row_count: int
    null_counts: dict[str, int] = field(default_factory=dict)
    duplicate_count: int = 0
    mpc_mismatches: list[str] = field(default_factory=list)
    out_of_range: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class DataValidator:
    """Validate water quality DataFrame on load."""

    def __init__(self, strict: bool = False) -> None:
        self.strict = strict

    def validate(self, df: pd.DataFrame) -> ValidationReport:
        """
        Run validation checks and return a report.

        Raises:
            ValueError: If strict=True and critical errors are found.
        """
        report = ValidationReport(passed=True, row_count=len(df))

        missing_cols = REQUIRED_COLUMNS - set(df.columns)
        if missing_cols:
            msg = f"Missing required columns: {sorted(missing_cols)}"
            report.errors.append(msg)
            report.passed = False

        if df.empty:
            report.errors.append("Dataset is empty")
            report.passed = False
            if self.strict:
                raise ValueError("; ".join(report.errors))
            return report

        report.null_counts = df.isnull().sum().to_dict()
        report.duplicate_count = int(df.duplicated().sum())

        if "Pollutant" in df.columns and "MPC" in df.columns:
            for pollutant, spec in POLLUTANTS.items():
                subset = df[df["Pollutant"] == pollutant]
                if subset.empty:
                    continue
                unique_mpc = subset["MPC"].dropna().unique()
                if len(unique_mpc) == 1 and float(unique_mpc[0]) != spec.mpc:
                    report.mpc_mismatches.append(
                        f"{pollutant}: file MPC={unique_mpc[0]}, expected={spec.mpc}"
                    )

        if "Concentration" in df.columns:
            neg = int((df["Concentration"] < 0).sum())
            if neg:
                report.out_of_range.append(f"Negative concentrations: {neg} rows")

        if "Ratio" in df.columns:
            high = int((df["Ratio"] > 10).sum())
            if high:
                report.warnings.append(f"Ratio > 10 (extreme): {high} rows")

        if "data_source" not in df.columns:
            report.warnings.append("Missing data_source provenance column")

        if report.mpc_mismatches:
            report.warnings.extend(report.mpc_mismatches)

        if report.duplicate_count > 0:
            report.warnings.append(f"Duplicate rows: {report.duplicate_count}")

        if report.errors:
            report.passed = False
            logger.error("Validation failed: %s", report.errors)
            if self.strict:
                raise ValueError("; ".join(report.errors))
        else:
            logger.info(
                "Validation passed: %d rows, %d duplicates, %d warnings",
                report.row_count,
                report.duplicate_count,
                len(report.warnings),
            )

        for w in report.warnings:
            logger.warning("Data quality: %s", w)

        return report
