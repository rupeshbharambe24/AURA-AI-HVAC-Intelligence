from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ...core.config import Settings
from ..bundles.loader import ModelRegistryService, load_market_bundle
from ..data.repository import DataRepository
from ..features.market_features import (
    build_market_feature_row,
    build_news_timeline,
    derive_tag_drivers,
    resolve_news_tags,
)


class MarketShareService:
    def __init__(self, repo: DataRepository, settings: Settings, registry: ModelRegistryService):
        self.repo = repo
        self.settings = settings
        self.registry = registry

    def get_options(self) -> Dict[str, Any]:
        products = self.repo.get_market_products()
        default_date = self.repo.get_market_share_latest_date()
        bundle = load_market_bundle(self.settings.MODEL_DIR, self.registry)
        return {
            "products": products,
            "supported_horizons_months": bundle.supported_horizons(),
            "default_as_of_date": default_date.strftime("%Y-%m-%d"),
        }

    def get_model_metrics(self) -> Tuple[Dict[str, Any], List[str]]:
        bundle = load_market_bundle(self.settings.MODEL_DIR, self.registry)
        meta_metrics = bundle.metadata.get("metrics") or []
        if meta_metrics:
            return {"metrics": meta_metrics}, []
        key_metric = bundle.metadata.get("key_metric")
        if key_metric:
            return {"metrics": [{"label": "Key Metric", "value": str(key_metric)}]}, []
        return {"metrics": []}, ["model-level metrics unavailable"]

    def predict(
        self,
        product_id: str,
        horizon_months: int,
        as_of_date: Optional[str],
        news_filters: Optional[Dict[str, bool]],
    ) -> Tuple[Dict[str, Any], List[str]]:
        warnings: List[str] = []
        bundle = load_market_bundle(self.settings.MODEL_DIR, self.registry)
        horizon_months = int(horizon_months)
        horizon_months = max(3, min(horizon_months, 6))

        series = self.repo.get_market_share_series(product_id)
        series = series.sort_values("date").reset_index(drop=True)
        latest = series["date"].max()

        if as_of_date:
            as_of = pd.to_datetime(as_of_date).to_period("M").to_timestamp()
        else:
            as_of = latest

        if as_of not in set(series["date"].tolist()):
            available = series[series["date"] <= as_of]
            if available.empty:
                as_of = latest
                warnings.append("as_of_date not found; using latest available date")
            else:
                as_of = available["date"].max()
                warnings.append("as_of_date not found; using nearest past date")

        last_actual = float(series[series["date"] == as_of].iloc[0]["market_share"])

        try:
            news_df = self.repo.load_news_dataframe()
        except FileNotFoundError:
            news_df = pd.DataFrame()
            warnings.append("news_corpus.json missing; news features set to zero")

        tags, tag_warnings = resolve_news_tags(news_filters)
        warnings.extend(tag_warnings)
        if tags and not news_df.empty:
            tag_set = set(tags)

            def _has_tag(row_tags):
                if not isinstance(row_tags, list):
                    return False
                return any(t in tag_set for t in row_tags)

            news_df = news_df[news_df["tags"].apply(_has_tag)].copy()

        try:
            reg_df = self.repo.get_regulations_for_product(product_id)
        except FileNotFoundError:
            reg_df = pd.DataFrame()
            warnings.append("regulatory_timeline.csv missing; regulatory features set to zero")

        try:
            ext_df = self.repo.load_external_signals()
        except FileNotFoundError:
            ext_df = pd.DataFrame()
            warnings.append("external_signals.csv missing; macro features set to zero")

        lag_values = _initial_lags(series, as_of, warnings)
        interval_std, interval_warning = _interval_std(series, as_of)
        if interval_warning:
            warnings.append(interval_warning)

        forecasts: List[Dict[str, Any]] = []
        max_model_horizon = min(horizon_months, 3)
        for step in range(1, max_model_horizon + 1):
            target_date = as_of + pd.DateOffset(months=step)
            row, row_warnings = build_market_feature_row(
                repo=self.repo,
                product_id=product_id,
                target_date=target_date,
                lag_values=lag_values,
                news_df=news_df,
                ext_df=ext_df,
                reg_df=reg_df,
                encoder=bundle.encoder,
            )
            warnings.extend(row_warnings)
            X = self._align_features(row, bundle.features)
            yhat = float(bundle.predict(X)[0])
            yhat = float(np.clip(yhat, 0.0, 100.0))
            lower, upper = _interval_bounds(yhat, interval_std)
            forecasts.append(
                {
                    "month": target_date.strftime("%Y-%m"),
                    "our_share": yhat,
                    "lower": lower,
                    "upper": upper,
                }
            )
            lag_values = [yhat] + lag_values[:-1]

        if horizon_months > 3:
            warnings.append("Horizon>3 is extrapolated; retrain for full fidelity")
            for step in range(4, horizon_months + 1):
                target_date = as_of + pd.DateOffset(months=step)
                yhat = _extrapolate(lag_values, step - 3)
                yhat = float(np.clip(yhat, 0.0, 100.0))
                lower, upper = _interval_bounds(yhat, interval_std)
                forecasts.append(
                    {
                        "month": target_date.strftime("%Y-%m"),
                        "our_share": yhat,
                        "lower": lower,
                        "upper": upper,
                    }
                )
                lag_values = [yhat] + lag_values[:-1]

        alerts = _build_alerts(forecasts, last_actual, horizon_months > 3)
        timeline_start = (as_of - pd.DateOffset(months=6)).to_period("M").to_timestamp()
        timeline_end = (as_of + pd.DateOffset(months=horizon_months)).to_period("M").to_timestamp()
        news_timeline = build_news_timeline(news_df, timeline_start, timeline_end)

        drivers = _drivers(bundle, news_df)
        if not drivers:
            warnings.append("Drivers are approximate (news-based)")
            drivers = derive_tag_drivers(news_df)

        metrics, metric_warnings = _backtest_metrics(
            series=series,
            as_of=as_of,
            repo=self.repo,
            product_id=product_id,
            news_df=news_df,
            ext_df=ext_df,
            reg_df=reg_df,
            bundle=bundle,
        )
        warnings.extend(metric_warnings)

        response = {
            "product_id": product_id,
            "as_of_date": as_of.strftime("%Y-%m-%d"),
            "horizon_months": horizon_months,
            "forecast": forecasts,
            "alerts": alerts,
            "news_timeline": news_timeline,
            "drivers": drivers,
            "metrics": metrics,
        }
        return response, warnings

    def predict_batch(self, df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], List[str]]:
        warnings: List[str] = []
        results: List[Dict[str, Any]] = []
        for _, row in df.iterrows():
            product_id = str(row.get("product_id"))
            horizon = int(row.get("horizon_months", 3))
            as_of_date = row.get("as_of_date")
            if isinstance(as_of_date, float) and np.isnan(as_of_date):
                as_of_date = None
            news_filters = None
            data, warn = self.predict(product_id, horizon, as_of_date, news_filters)
            warnings.extend(warn)
            results.append(data)
        return results, warnings

    def _align_features(self, row: Dict[str, float], feature_cols: List[str]) -> pd.DataFrame:
        X = pd.DataFrame([{c: row.get(c, 0.0) for c in feature_cols}])
        return X


def _initial_lags(series: pd.DataFrame, as_of: pd.Timestamp, warnings: List[str]) -> List[float]:
    hist = series[series["date"] <= as_of].sort_values("date")
    values = hist["market_share"].astype(float).tolist()
    lags: List[float] = []
    for i in range(1, 7):
        if len(values) >= i:
            lags.append(float(values[-i]))
        else:
            lags.append(float(np.mean(values)) if values else 0.0)
    if len(values) < 6:
        warnings.append("Insufficient history for full share lags; padding with averages")
    return lags


def _interval_std(series: pd.DataFrame, as_of: pd.Timestamp) -> Tuple[float, Optional[str]]:
    hist = series[series["date"] <= as_of].sort_values("date")
    tail = hist.tail(12)
    if len(tail) < 3:
        return 0.5, "Intervals are approximate (limited history)"
    std = float(np.std(tail["market_share"].astype(float)))
    if std == 0:
        return 0.5, "Intervals are approximate (zero variance)"
    return std, "Intervals are approximate (residual-based)"


def _interval_bounds(pred: float, std: float) -> Tuple[float, float]:
    z = 1.645
    lower = max(0.0, pred - z * std)
    upper = min(100.0, pred + z * std)
    return float(lower), float(upper)


def _extrapolate(lag_values: List[float], step: int) -> float:
    if len(lag_values) < 2:
        return lag_values[0] if lag_values else 0.0
    deltas = []
    for i in range(min(3, len(lag_values) - 1)):
        deltas.append(lag_values[i] - lag_values[i + 1])
    delta = float(np.mean(deltas)) if deltas else 0.0
    damp = 0.6 ** max(step - 1, 0)
    return lag_values[0] + delta * damp


def _build_alerts(forecasts: List[Dict[str, Any]], last_actual: float, extrapolated: bool) -> List[Dict[str, str]]:
    alerts: List[Dict[str, str]] = []
    if not forecasts:
        return alerts
    diff = forecasts[-1]["our_share"] - last_actual
    if diff <= -1.0:
        alerts.append({"type": "risk_drop", "message": "Predicted share drop exceeds 1pt", "severity": "high"})
    elif diff >= 1.0:
        alerts.append({"type": "upside_gain", "message": "Predicted share gain exceeds 1pt", "severity": "medium"})
    else:
        alerts.append({"type": "watch", "message": "Share change within normal range", "severity": "low"})

    if extrapolated:
        alerts.append({"type": "watch", "message": "Horizon extrapolated; monitor trends", "severity": "low"})
    return alerts


def _drivers(bundle, news_df: pd.DataFrame) -> List[Dict[str, float]]:
    model = bundle.model
    if hasattr(model, "feature_importances_"):
        importances = getattr(model, "feature_importances_")
        if importances is not None:
            pairs = list(zip(bundle.features, np.asarray(importances, dtype=float)))
            pairs = sorted(pairs, key=lambda x: x[1], reverse=True)
            top = pairs[:5]
            total = float(np.sum([v for _, v in top])) if top else 0.0
            if total > 0:
                return [
                    {"name": _map_feature_name(f), "importance_pct": float(v / total * 100.0)}
                    for f, v in top
                ]
    return []


def _backtest_metrics(
    series: pd.DataFrame,
    as_of: pd.Timestamp,
    repo: DataRepository,
    product_id: str,
    news_df: pd.DataFrame,
    ext_df: pd.DataFrame,
    reg_df: pd.DataFrame,
    bundle,
    window: int = 6,
) -> Tuple[Dict[str, Optional[float]], List[str]]:
    warnings: List[str] = []
    hist = series[series["date"] <= as_of].sort_values("date").reset_index(drop=True)
    if len(hist) < max(window + 2, 4):
        return {
            "mae_pct": None,
            "rmse_pct": None,
            "mape_pct": None,
            "coverage_pct": None,
        }, ["metrics unavailable (insufficient history)"]

    target_dates = hist["date"].tail(window).tolist()
    preds: List[float] = []
    actuals: List[float] = []
    lowers: List[float] = []
    uppers: List[float] = []

    date_set = set(hist["date"].tolist())
    for target_date in target_dates:
        as_of_date = (target_date - pd.DateOffset(months=1)).to_period("M").to_timestamp()
        if as_of_date not in date_set:
            continue
        lag_values = _initial_lags(hist, as_of_date, warnings)
        row, row_warnings = build_market_feature_row(
            repo=repo,
            product_id=product_id,
            target_date=target_date,
            lag_values=lag_values,
            news_df=news_df,
            ext_df=ext_df,
            reg_df=reg_df,
            encoder=bundle.encoder,
        )
        warnings.extend(row_warnings)
        X = pd.DataFrame([{c: row.get(c, 0.0) for c in bundle.features}])
        yhat = float(bundle.predict(X)[0])
        yhat = float(np.clip(yhat, 0.0, 100.0))
        std, _ = _interval_std(hist, as_of_date)
        lower, upper = _interval_bounds(yhat, std)

        actual_row = hist[hist["date"] == target_date]
        if actual_row.empty:
            continue
        actual = float(actual_row.iloc[0]["market_share"])
        preds.append(yhat)
        actuals.append(actual)
        lowers.append(lower)
        uppers.append(upper)

    if len(actuals) < 3:
        return {
            "mae_pct": None,
            "rmse_pct": None,
            "mape_pct": None,
            "coverage_pct": None,
        }, ["metrics unavailable (insufficient backtest points)"]

    actuals_arr = np.asarray(actuals, dtype=float)
    preds_arr = np.asarray(preds, dtype=float)
    eps = 1e-6
    mae = float(np.mean(np.abs(preds_arr - actuals_arr)))
    rmse = float(np.sqrt(np.mean((preds_arr - actuals_arr) ** 2)))
    mape = float(np.mean(np.abs(preds_arr - actuals_arr) / np.maximum(np.abs(actuals_arr), eps)) * 100.0)
    lower_arr = np.asarray(lowers, dtype=float)
    upper_arr = np.asarray(uppers, dtype=float)
    coverage = float(np.mean((actuals_arr >= lower_arr) & (actuals_arr <= upper_arr)) * 100.0)

    return {
        "mae_pct": round(mae, 2),
        "rmse_pct": round(rmse, 2),
        "mape_pct": round(mape, 2),
        "coverage_pct": round(coverage, 2),
    }, warnings


def _map_feature_name(feature: str) -> str:
    if feature.startswith("share_lag"):
        return "Recent share"
    if feature in ("news_volume", "avg_sentiment"):
        return "News signal"
    if feature in ("months_since_announcement", "months_until_effective", "reg_active", "reg_impact"):
        return "Regulatory impact"
    if feature.endswith("_lag3"):
        return "Macro signals"
    if feature == "product_encoded":
        return "Product effect"
    if feature in ("year", "month_num"):
        return "Seasonality"
    return feature
