from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..data.repository import DataRepository


MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]


@dataclass
class ScenarioResult:
    applied: Dict[str, Dict[str, float]]
    warnings: List[str]


def build_forecast_features(
    repo: DataRepository,
    product_id: str,
    aps: str,
    cutoff_date: pd.Timestamp,
    horizons: List[int],
    scenario: Optional[Dict[str, float]],
    exog_future_mode: str,
) -> Tuple[pd.DataFrame, ScenarioResult, List[str]]:
    warnings: List[str] = []
    scenario = scenario or {}

    series = repo.get_series(product_id, aps)
    series = series.sort_values("date").reset_index(drop=True)

    if cutoff_date not in set(series["date"].tolist()):
        available = series[series["date"] <= cutoff_date]
        if available.empty:
            cutoff_date = series["date"].max()
            warnings.append("cutoff_date not found; using latest available date")
        else:
            cutoff_date = available["date"].max()
            warnings.append("cutoff_date not found; using nearest past date")

    cutoff_row = series[series["date"] == cutoff_date].iloc[0]
    base = {
        "product": product_id,
        "aps": aps,
        "series_id": f"{product_id}|{aps}",
        "date": cutoff_date,
        "year": int(cutoff_date.year),
        "month_num": int(cutoff_date.month),
        "quarter": int(((cutoff_date.month - 1) // 3) + 1),
    }

    series_idx = series.set_index("date")

    # demand lags
    for lag in range(0, 13):
        lag_date = cutoff_date - pd.DateOffset(months=lag)
        val = series_idx["demand"].get(lag_date, np.nan)
        base[f"demand_lag{lag}"] = float(val) if pd.notna(val) else np.nan

    # rolling stats (include cutoff date)
    for w in [3, 6, 12]:
        hist = series[(series["date"] <= cutoff_date)].tail(w)
        base[f"demand_roll_mean_{w}"] = float(hist["demand"].mean()) if not hist.empty else np.nan
        base[f"demand_roll_std_{w}"] = float(hist["demand"].std()) if len(hist) > 1 else np.nan

    base["demand_diff_1"] = base.get("demand_lag0", np.nan) - base.get("demand_lag1", np.nan)
    base["demand_diff_12"] = base.get("demand_lag0", np.nan) - base.get("demand_lag12", np.nan)
    base["month_sin"] = float(np.sin(2 * np.pi * base["month_num"] / 12.0))
    base["month_cos"] = float(np.cos(2 * np.pi * base["month_num"] / 12.0))

    ext = repo.load_external_signals()
    ext = _prepare_exog_features(ext)

    applied = {}
    scenario_warnings: List[str] = []

    rows = []
    for h in horizons:
        target_date = cutoff_date + pd.DateOffset(months=h)
        row = dict(base)
        row["horizon"] = int(h)
        row["target_date"] = target_date

        exog_row, exog_warn = _select_exog_row(
            ext, cutoff_date, target_date, exog_future_mode
        )
        if exog_warn:
            warnings.append(exog_warn)

        exog_row = exog_row.copy()
        sc_applied, sc_warn = _apply_scenarios(exog_row, scenario)
        if sc_warn:
            scenario_warnings.extend(sc_warn)
        if sc_applied:
            applied.update(sc_applied)

        for c, v in exog_row.items():
            if c == "date":
                continue
            row[c] = v

        rows.append(row)

    warnings.extend(scenario_warnings)

    features = pd.DataFrame(rows)
    scenario_result = ScenarioResult(applied=applied, warnings=scenario_warnings)
    return features, scenario_result, warnings


def _prepare_exog_features(ext: pd.DataFrame) -> pd.DataFrame:
    ext = ext.copy()
    ext["date"] = pd.to_datetime(ext["date"]).dt.to_period("M").dt.to_timestamp()
    ext = ext.sort_values("date").reset_index(drop=True)

    ignore_cols = {"date", "year", "month", "month_num"}
    exog_cols = [c for c in ext.columns if c not in ignore_cols and pd.api.types.is_numeric_dtype(ext[c])]

    for col in exog_cols:
        for lag in [0, 1, 3, 6, 12]:
            ext[f"{col}_lag{lag}"] = ext[col].shift(lag)

    keep_cols = ["date"] + [c for c in ext.columns if c.endswith(tuple([f"_lag{l}" for l in [0,1,3,6,12]]))]
    return ext[keep_cols]


def _select_exog_row(
    ext: pd.DataFrame,
    cutoff_date: pd.Timestamp,
    target_date: pd.Timestamp,
    exog_future_mode: str,
) -> Tuple[pd.Series, Optional[str]]:
    if exog_future_mode == "known":
        row = ext[ext["date"] == target_date]
        if not row.empty:
            return row.iloc[0], None
        fallback = ext[ext["date"] <= cutoff_date]
        if not fallback.empty:
            return fallback.iloc[-1], "future exog not found; using last-known exog"
        return ext.iloc[-1], "future exog not found; using last available exog"

    # last_known
    row = ext[ext["date"] <= cutoff_date]
    if not row.empty:
        return row.iloc[-1], None
    return ext.iloc[-1], "exog not found at cutoff; using last available exog"


def _apply_scenarios(exog_row: pd.Series, scenario: Dict[str, float]) -> Tuple[Dict[str, Dict[str, float]], List[str]]:
    applied: Dict[str, Dict[str, float]] = {}
    warnings: List[str] = []

    temp_pct = float(scenario.get("temperature_pct", 0.0))
    housing_pct = float(scenario.get("housing_growth_pct", 0.0))

    if temp_pct != 0.0:
        if "cooling_degree_days_lag0" in exog_row:
            mult = 1.0 + temp_pct / 100.0
            exog_row["cooling_degree_days_lag0"] *= mult
            applied["cooling_degree_days_lag0"] = {"multiplier": mult}
        elif "avg_temp_f_lag0" in exog_row:
            mult = 1.0 + temp_pct / 100.0
            exog_row["avg_temp_f_lag0"] *= mult
            applied["avg_temp_f_lag0"] = {"multiplier": mult}
        else:
            warnings.append("temperature_pct provided but no temperature columns found")

        if "heating_degree_days_lag0" in exog_row:
            mult = 1.0 - temp_pct / 100.0
            exog_row["heating_degree_days_lag0"] *= mult
            applied["heating_degree_days_lag0"] = {"multiplier": mult}

    if housing_pct != 0.0:
        if "housing_starts_k_lag0" in exog_row:
            mult = 1.0 + housing_pct / 100.0
            exog_row["housing_starts_k_lag0"] *= mult
            applied["housing_starts_k_lag0"] = {"multiplier": mult}
        else:
            warnings.append("housing_growth_pct provided but housing_starts_k not found")

        if "building_permits_k_lag0" in exog_row:
            mult = 1.0 + housing_pct / 100.0
            exog_row["building_permits_k_lag0"] *= mult
            applied["building_permits_k_lag0"] = {"multiplier": mult}
        else:
            warnings.append("housing_growth_pct provided but building_permits_k not found")

    return applied, warnings
