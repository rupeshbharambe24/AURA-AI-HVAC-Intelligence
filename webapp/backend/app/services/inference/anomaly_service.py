from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ...core.config import Settings
from ..bundles.loader import (
    AnomalyBundleAdapter,
    ModelRegistryService,
    load_anomaly_bundle,
    load_forecast_bundle,
)
from ..data.repository import DataRepository
from ..features.forecast_features import _prepare_exog_features


class AnomalyService:
    def __init__(self, repo: DataRepository, settings: Settings, registry: ModelRegistryService):
        self.repo = repo
        self.settings = settings
        self.registry = registry

    def get_options(self) -> Dict[str, Any]:
        adapter = load_anomaly_bundle(self.settings.MODEL_DIR, self.registry)
        return {
            "products": self.repo.get_products(),
            "aps_list": self.repo.get_aps_list(None),
            "default_thresholds": adapter.default_thresholds(),
        }

    def detect(
        self,
        product_id: str,
        aps: str,
        date_range: Optional[List[str]],
        thresholds: Optional[Dict[str, float]],
        threshold: Optional[float],
        include_explanations: bool,
    ) -> Tuple[Dict[str, Any], List[str]]:
        warnings: List[str] = []

        adapter = load_anomaly_bundle(self.settings.MODEL_DIR, self.registry)
        defaults = adapter.default_thresholds()

        if thresholds:
            eff = {
                "point": float(thresholds.get("point", defaults["point"])),
                "pattern": float(thresholds.get("pattern", defaults["pattern"])),
                "trend": float(thresholds.get("trend", defaults["trend"])),
            }
        elif threshold is not None:
            eff = {
                "point": float(threshold),
                "pattern": float(defaults["pattern"]),
                "trend": float(defaults["trend"]),
            }
            warnings.append("pattern/trend thresholds defaulted")
        else:
            eff = defaults
            warnings.append("thresholds defaulted from bundle")

        series = self.repo.get_series(product_id, aps)
        start, end = self._resolve_range(series, date_range)
        series = series[(series["date"] >= start) & (series["date"] <= end)].copy()
        if series.empty:
            raise ValueError("No data available for requested date_range")

        expected, baseline_method, baseline_warnings = self._baseline_expected(product_id, aps, series)
        warnings.extend(baseline_warnings)

        residual = series["demand"].values - expected
        series["expected"] = expected
        series["residual"] = residual

        point_score = _point_score(series["residual"])
        pattern_score = _pattern_score(series["residual"], series["date"])
        trend_score = _trend_score(series["residual"])

        series["point_score"] = point_score
        series["pattern_score"] = pattern_score
        series["trend_score"] = trend_score
        series["anomaly_score"] = np.maximum.reduce([point_score, pattern_score, trend_score])

        promos = self.repo.get_promos(product_id, aps, start, end)
        capacity = self.repo.get_capacity(product_id, aps, start, end)

        rows = []
        for _, row in series.iterrows():
            family = _family(row, eff)
            is_anomaly = family != "normal"
            evidence = []
            anomaly_type = None
            root_cause = None
            explanation = None

            if is_anomaly and include_explanations:
                evidence = _build_evidence(row, promos, capacity)
                anomaly_type, root_cause = _anomaly_type_and_cause(family, evidence)
                explanation = _build_explanation(row, evidence, root_cause)

            rows.append(
                {
                    "date": row["date"].strftime("%Y-%m-%d"),
                    "demand": float(row["demand"]),
                    "expected": float(row["expected"]),
                    "residual": float(row["residual"]),
                    "anomaly_score": float(row["anomaly_score"]),
                    "is_anomaly": bool(is_anomaly),
                    "anomaly_family": None if family == "normal" else family,
                    "anomaly_type": anomaly_type,
                    "root_cause": root_cause,
                    "explanation": explanation,
                    "evidence": evidence,
                }
            )

        summary = _summary(rows)

        response = {
            "product_id": product_id,
            "aps": aps,
            "baseline_method": baseline_method,
            "effective_thresholds": eff,
            "series": rows,
            "summary": summary,
        }
        return response, warnings

    def detect_batch(
        self,
        df: pd.DataFrame,
        thresholds: Optional[Dict[str, float]],
        threshold: Optional[float],
        include_explanations: bool,
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        warnings: List[str] = []
        results: List[Dict[str, Any]] = []
        for (pid, aps), g in df.groupby(["product_id", "aps"]):
            date_range = [g["date"].min().strftime("%Y-%m-%d"), g["date"].max().strftime("%Y-%m-%d")]
            res, w = self.detect(
                product_id=pid,
                aps=aps,
                date_range=date_range,
                thresholds=thresholds,
                threshold=threshold,
                include_explanations=include_explanations,
            )
            warnings.extend(w)
            results.append(res)
        return results, warnings

    def get_model_metrics(self) -> Tuple[Dict[str, Any], List[str]]:
        adapter = load_anomaly_bundle(self.settings.MODEL_DIR, self.registry)
        meta_metrics = adapter.metadata.get("metrics") or []
        if meta_metrics:
            return {"metrics": meta_metrics}, []
        key_metric = adapter.metadata.get("key_metric")
        if key_metric:
            return {"metrics": [{"label": "Key Metric", "value": str(key_metric)}]}, []
        return {"metrics": []}, ["model-level metrics unavailable"]

    def _baseline_expected(
        self, product_id: str, aps: str, series: pd.DataFrame
    ) -> Tuple[np.ndarray, str, List[str]]:
        warnings: List[str] = []
        baseline_method = "forecast_service"

        try:
            _ = load_anomaly_bundle(self.settings.MODEL_DIR, self.registry)

            series_sorted = series.sort_values("date").reset_index(drop=True)
            feat = _build_cutoff_features(series_sorted, product_id, aps)
            forecast_adapter = load_forecast_bundle(self.settings.MODEL_DIR, self.registry)

            ext = _prepare_exog_features(self.repo.load_external_signals())
            ext = ext.sort_values("date").reset_index(drop=True)

            rows = []
            fallback_idx = []
            for i, dt in enumerate(series_sorted["date"].tolist()):
                cutoff = (dt - pd.DateOffset(months=1)).to_period("M").to_timestamp()
                match = feat[feat["date"] == cutoff]
                if match.empty:
                    fallback_idx.append(i)
                    continue
                row = match.iloc[0].to_dict()
                row["horizon"] = 1
                row["target_date"] = dt
                exog_row = ext[ext["date"] == dt]
                if not exog_row.empty:
                    for c, v in exog_row.iloc[0].items():
                        if c != "date":
                            row[c] = v
                rows.append(row)

            cutoff_df = pd.DataFrame(rows)
            if cutoff_df.isna().any().any():
                warnings.append("missing external signals for some dates; using last known where possible")
                cutoff_df = cutoff_df.ffill()

            X = cutoff_df.copy()
            for c in forecast_adapter.feature_cols:
                if c not in X.columns:
                    X[c] = np.nan
            X = X[forecast_adapter.feature_cols]
            for c in forecast_adapter.cat_cols:
                if c in X.columns:
                    X[c] = X[c].astype("category")

            yhat = forecast_adapter.predict(X)
            expected = np.zeros(len(series_sorted), dtype=float)
            pred_idx = [i for i in range(len(series_sorted)) if i not in fallback_idx]
            expected[pred_idx] = np.clip(np.asarray(yhat, dtype=float), 0, None)

            if fallback_idx:
                warnings.append("baseline fallback for early dates; seasonal naive used")
                seasonal = _seasonal_naive(series_sorted)
                expected[fallback_idx] = seasonal[fallback_idx]

            return expected, baseline_method, warnings
        except Exception:
            warnings.append("forecast_service baseline failed; using seasonal naive")
            expected = _seasonal_naive(series)
            return np.asarray(expected, dtype=float), "seasonal_naive", warnings

    def _resolve_range(self, series: pd.DataFrame, date_range: Optional[List[str]]):
        if not date_range:
            return series["date"].min(), series["date"].max()
        start = pd.to_datetime(date_range[0]).to_period("M").to_timestamp()
        end = pd.to_datetime(date_range[1]).to_period("M").to_timestamp()
        return start, end


def _point_score(residual: pd.Series, window: int = 24) -> np.ndarray:
    med = residual.rolling(window=window, min_periods=6).median()
    mad = (residual - med).abs().rolling(window=window, min_periods=6).median()
    scale = mad * 1.4826
    scale = scale.replace(0, np.nan)
    z = (residual - med).abs() / scale
    z = z.fillna(0.0)
    return z.to_numpy(dtype=float)


def _pattern_score(residual: pd.Series, dates: pd.Series) -> np.ndarray:
    df = pd.DataFrame({"residual": residual, "month": dates.dt.month, "date": dates})
    scores = []
    for _, row in df.iterrows():
        hist = df[(df["month"] == row["month"]) & (df["date"] < row["date"])]
        if len(hist) < 2:
            scores.append(0.0)
            continue
        mean = hist["residual"].mean()
        std = hist["residual"].std() or 1.0
        scores.append(abs(row["residual"] - mean) / std)
    return np.asarray(scores, dtype=float)


def _trend_score(residual: pd.Series, w_short: int = 3, w_long: int = 12) -> np.ndarray:
    short = residual.rolling(window=w_short, min_periods=2).mean()
    long = residual.rolling(window=w_long, min_periods=4).mean()
    diff = (short - long).abs()
    denom = residual.rolling(window=w_long, min_periods=4).std().replace(0, np.nan)
    score = (diff / denom).fillna(0.0)
    return score.to_numpy(dtype=float)


def _family(row: pd.Series, th: Dict[str, float]) -> str:
    if row["trend_score"] > th["trend"]:
        return "trend_break"
    if row["pattern_score"] > th["pattern"]:
        return "pattern_shift"
    if row["point_score"] > th["point"]:
        return "demand_spike" if row["residual"] > 0 else "demand_drop"
    return "normal"


def _build_evidence(row: pd.Series, promos: pd.DataFrame, capacity: pd.DataFrame) -> List[Dict[str, Any]]:
    evidence = []
    date = row["date"]
    promo_hit = promos[promos["date"] == date]
    if not promo_hit.empty:
        evidence.append(
            {
                "type": "promotion",
                "strength": 0.7,
                "detail": "Promotion active in same month",
                "ref": str(promo_hit.iloc[0].get("event_id", "")) or None,
            }
        )

    cap_hit = capacity[capacity["date"] == date]
    if not cap_hit.empty:
        cap_val = float(cap_hit.iloc[0].get("capacity_units", cap_hit.iloc[0].get("capacity", 0)))
        if cap_val and cap_val < float(row["expected"]):
            evidence.append(
                {
                    "type": "capacity",
                    "strength": 0.6,
                    "detail": "Capacity below expected demand",
                    "ref": None,
                }
            )

    if not evidence:
        evidence.append(
            {
                "type": "statistical",
                "strength": 0.3,
                "detail": "Statistical deviation from expected pattern",
                "ref": None,
            }
        )
    return evidence


def _anomaly_type_and_cause(family: str, evidence: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[str]]:
    types = {e["type"] for e in evidence}
    if family == "demand_spike":
        if "promotion" in types:
            return "spike_promo", "Promotion-driven spike"
        if "capacity" in types:
            return "spike_prebuy", "Prebuy/rebound due to capacity constraints"
        return "spike_prebuy", "Unexpected spike"
    if family == "demand_drop":
        if "capacity" in types:
            return "drop_shortage", "Supply or capacity shortage"
        return "drop_competition", "Market/competition-driven drop"
    if family == "pattern_shift":
        return "pattern_shift", "Seasonality profile changed"
    if family == "trend_break":
        return "trend_break", "Underlying trend shifted"
    return None, None


def _build_explanation(row: pd.Series, evidence: List[Dict[str, Any]], root: Optional[str]) -> str:
    parts = [
        f"Observed {row['demand']:.1f} vs expected {row['expected']:.1f}.",
        f"Residual {row['residual']:.1f}.",
    ]
    if root:
        parts.append(root)
    if evidence:
        parts.append(f"Evidence: {', '.join([e['type'] for e in evidence])}.")
    return " ".join(parts)


def _summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(rows)
    anomalies = sum(1 for r in rows if r["is_anomaly"])
    by_family: Dict[str, int] = {}
    for r in rows:
        fam = r["anomaly_family"]
        if not fam:
            continue
        by_family[fam] = by_family.get(fam, 0) + 1
    return {"total": total, "anomalies": anomalies, "by_family": by_family}


def _seasonal_naive(series: pd.DataFrame) -> np.ndarray:
    s = series.set_index("date")["demand"]
    out = []
    for dt in series["date"]:
        prev = dt - pd.DateOffset(months=12)
        if prev in s.index:
            out.append(float(s.loc[prev]))
        else:
            out.append(float(s.loc[:dt].iloc[-1]))
    return np.asarray(out, dtype=float)


def _build_cutoff_features(series: pd.DataFrame, product_id: str, aps: str) -> pd.DataFrame:
    df = series.copy()
    df["product"] = product_id
    df["aps"] = aps
    df["series_id"] = f"{product_id}|{aps}"
    df["year"] = df["date"].dt.year
    df["month_num"] = df["date"].dt.month
    df["quarter"] = ((df["month_num"] - 1) // 3 + 1).astype(int)
    df["month_sin"] = np.sin(2 * np.pi * df["month_num"] / 12.0)
    df["month_cos"] = np.cos(2 * np.pi * df["month_num"] / 12.0)

    df = df.sort_values("date").reset_index(drop=True)

    for lag in range(0, 13):
        df[f"demand_lag{lag}"] = df["demand"].shift(lag)

    for w in [3, 6, 12]:
        df[f"demand_roll_mean_{w}"] = df["demand"].rolling(window=w, min_periods=max(2, w // 2)).mean()
        df[f"demand_roll_std_{w}"] = df["demand"].rolling(window=w, min_periods=max(2, w // 2)).std()

    df["demand_diff_1"] = df["demand"] - df["demand_lag1"]
    df["demand_diff_12"] = df["demand"] - df["demand_lag12"]
    return df
