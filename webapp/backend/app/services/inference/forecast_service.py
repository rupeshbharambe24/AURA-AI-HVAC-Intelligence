from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ...core.config import Settings
from ..bundles.loader import ForecastBundleAdapter, ModelRegistryService, load_forecast_bundle
from ..data.repository import DataRepository
from ..features.forecast_features import build_forecast_features


class ForecastService:
    def __init__(self, repo: DataRepository, settings: Settings, registry: ModelRegistryService):
        self.repo = repo
        self.settings = settings
        self.registry = registry

    def get_options(self) -> Dict[str, Any]:
        products = self.repo.get_products()
        aps_list = self.repo.get_aps_list(None)
        return {
            "products": products,
            "aps_list": aps_list,
            "max_horizon_months": 12,
        }

    def predict(
        self,
        product_id: str,
        aps: str,
        horizon_months: int,
        cutoff_date: Optional[str],
        scenarios: Optional[Dict[str, float]],
        include_actuals: bool,
        include_explain: bool,
    ) -> Tuple[Dict[str, Any], List[str]]:
        warnings: List[str] = []

        horizon_months = max(1, min(int(horizon_months), 12))

        series = self.repo.get_series(product_id, aps)
        latest = series["date"].max()
        if cutoff_date:
            cutoff = pd.to_datetime(cutoff_date).to_period("M").to_timestamp()
        else:
            cutoff = latest

        horizons = list(range(1, horizon_months + 1))

        features, scenario_result, feature_warnings = build_forecast_features(
            repo=self.repo,
            product_id=product_id,
            aps=aps,
            cutoff_date=cutoff,
            horizons=horizons,
            scenario=scenarios,
            exog_future_mode=self.settings.EXOG_FUTURE_MODE,
        )
        warnings.extend(feature_warnings)

        bundle = load_forecast_bundle(self.settings.MODEL_DIR, self.registry)
        X = self._align_features(features, bundle.feature_cols, bundle.cat_cols)

        y_pred_model = bundle.predict(X)

        w_model, w_naive = bundle.get_ensemble_weights()
        if w_naive > 0:
            seasonal = _seasonal_naive_from_rows(features)
            y_pred = w_model * y_pred_model + w_naive * seasonal
        else:
            y_pred = y_pred_model

        y_pred = np.clip(np.asarray(y_pred, dtype=float), 0, None)

        lower, upper, interval_warning = self._intervals(features, y_pred, series)
        if interval_warning:
            warnings.append(interval_warning)

        forecast_rows = []
        for i, h in enumerate(horizons):
            target_date = (cutoff + pd.DateOffset(months=h)).to_period("M").to_timestamp()
            actual = None
            if include_actuals:
                match = series[series["date"] == target_date]
                if not match.empty:
                    actual = float(match.iloc[0]["demand"])

            drivers = self._drivers(series, cutoff, scenarios)
            forecast_rows.append(
                {
                    "date": target_date.strftime("%Y-%m"),
                    "actual": actual,
                    "predicted": float(y_pred[i]),
                    "lower": float(lower[i]) if lower is not None else None,
                    "upper": float(upper[i]) if upper is not None else None,
                    "drivers": drivers,
                }
            )

        metrics = self._metrics(forecast_rows)
        if metrics.get("warnings"):
            warnings.extend(metrics.pop("warnings"))

        explain = {}
        if include_explain:
            explain, explain_warnings = self._explain(bundle)
            warnings.extend(explain_warnings)

        response = {
            "model_id": bundle.metadata.get("id", "demand_forecast_prod"),
            "product_id": product_id,
            "aps": aps,
            "cutoff_date": cutoff.strftime("%Y-%m-%d"),
            "forecast": forecast_rows,
            "metrics": metrics,
            "explain": explain if include_explain else None,
            "applied_scenarios": scenario_result.applied,
        }
        return response, warnings

    def get_model_metrics(self) -> Tuple[Dict[str, Any], List[str]]:
        bundle = load_forecast_bundle(self.settings.MODEL_DIR, self.registry)
        meta_metrics = bundle.metadata.get("metrics") or []
        if meta_metrics:
            return {"metrics": meta_metrics}, []

        key_metric = bundle.metadata.get("key_metric")
        if key_metric:
            return {"metrics": [{"label": "Key Metric", "value": str(key_metric)}]}, []

        warnings = ["model-level metrics unavailable"]
        return {"metrics": []}, warnings

    def _align_features(self, df: pd.DataFrame, feature_cols: List[str], cat_cols: List[str]) -> pd.DataFrame:
        X = df.copy()
        for c in feature_cols:
            if c not in X.columns:
                X[c] = np.nan
        X = X[feature_cols]
        for c in cat_cols:
            if c in X.columns:
                X[c] = X[c].astype("category")
        return X

    def _intervals(self, features: pd.DataFrame, y_pred: np.ndarray, series: pd.DataFrame):
        # No quantile model available; approximate using seasonal naive residuals.
        seasonal = _seasonal_naive_from_rows(features)
        residuals = []
        for i, h in enumerate(features["horizon"].tolist()):
            target_date = features.iloc[i]["target_date"]
            match = series[series["date"] == target_date]
            if not match.empty:
                actual = float(match.iloc[0]["demand"])
                residuals.append(actual - seasonal[i])

        if len(residuals) < 3:
            return None, None, "Intervals are approximate (insufficient residuals)"

        std = float(np.std(residuals))
        z = 1.645  # ~90% interval
        lower = np.clip(y_pred - z * std, 0, None)
        upper = np.clip(y_pred + z * std, 0, None)
        return lower, upper, "Intervals are approximate (residual-based)"

    def _metrics(self, forecast_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        actuals = [r["actual"] for r in forecast_rows if r["actual"] is not None]
        preds = [r["predicted"] for r in forecast_rows if r["actual"] is not None]
        out: Dict[str, Any] = {"mape": None, "rmse": None, "coverage_95": None, "bias_pct": None}
        warnings: List[str] = []
        if not actuals:
            warnings.append("metrics unavailable (no actuals)")
            out["warnings"] = warnings
            return out

        actuals_arr = np.asarray(actuals, dtype=float)
        preds_arr = np.asarray(preds, dtype=float)
        eps = 1e-6
        out["mape"] = float(np.mean(np.abs(actuals_arr - preds_arr) / np.maximum(np.abs(actuals_arr), eps)) * 100.0)
        out["rmse"] = float(np.sqrt(np.mean((actuals_arr - preds_arr) ** 2)))
        out["bias_pct"] = float(np.mean((preds_arr - actuals_arr) / np.maximum(np.abs(actuals_arr), eps)) * 100.0)

        # Coverage requires intervals present
        lower = [r["lower"] for r in forecast_rows if r["actual"] is not None]
        upper = [r["upper"] for r in forecast_rows if r["actual"] is not None]
        if all(v is not None for v in lower + upper):
            low = np.asarray(lower, dtype=float)
            up = np.asarray(upper, dtype=float)
            within = (actuals_arr >= low) & (actuals_arr <= up)
            out["coverage_95"] = float(np.mean(within) * 100.0)
        else:
            warnings.append("coverage unavailable (intervals missing)")

        if warnings:
            out["warnings"] = warnings
        return out

    def _drivers(self, series: pd.DataFrame, cutoff: pd.Timestamp, scenarios: Optional[Dict[str, float]]) -> List[str]:
        drivers = []
        if scenarios and any(abs(v) > 0 for v in scenarios.values()):
            drivers.append("Scenario adjustment")

        hist = series[series["date"] <= cutoff].tail(3)
        if len(hist) >= 2:
            trend = hist["demand"].iloc[-1] - hist["demand"].iloc[0]
            if trend > 0:
                drivers.append("Recent trend up")
            elif trend < 0:
                drivers.append("Recent trend down")

        month = cutoff.month
        if month in (11, 12, 1, 2):
            drivers.append("Seasonality")
        return drivers or ["Seasonality"]

    def _explain(self, bundle: ForecastBundleAdapter) -> Tuple[Dict[str, Any], List[str]]:
        warnings: List[str] = []
        global_imp = bundle.global_importance()
        explain = {"global": [], "local": []}
        if global_imp:
            explain["global"] = global_imp[:10]
        else:
            warnings.append("Explainability unavailable; using heuristic drivers")
        return explain, warnings


def _seasonal_naive_from_rows(features: pd.DataFrame) -> np.ndarray:
    # seasonal naive from demand_lag(12-h)
    seasonal = []
    for _, row in features.iterrows():
        h = int(row["horizon"])
        lag_idx = 12 - h
        col = f"demand_lag{lag_idx}"
        val = row.get(col, np.nan)
        seasonal.append(float(val) if pd.notna(val) else float(row.get("demand_lag0", 0.0)))
    return np.asarray(seasonal, dtype=float)
