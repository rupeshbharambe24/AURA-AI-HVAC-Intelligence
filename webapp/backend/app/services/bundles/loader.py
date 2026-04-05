from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np

_forecast_cache: Optional[ForecastBundleAdapter] = None
_forecast_mtime: Optional[float] = None
_forecast_path: Optional[Path] = None


@dataclass
class AnomalyBundleAdapter:
    config: Dict[str, Any]
    metadata: Dict[str, Any]

    def default_thresholds(self) -> Dict[str, float]:
        return {
            "point": float(self.config.get("point_th", 3.0)),
            "pattern": float(self.config.get("pattern_th", 0.5)),
            "trend": float(self.config.get("trend_th", 1.5)),
        }

    def period(self) -> int:
        return int(self.config.get("period", 12))


_anomaly_cache: Optional[AnomalyBundleAdapter] = None
_anomaly_mtime: Optional[float] = None
_anomaly_path: Optional[Path] = None


@dataclass
class OptimizeBundleAdapter:
    artifact: Dict[str, Any]
    metadata: Dict[str, Any]

    @property
    def baseline_models(self):
        return self.artifact.get("baseline_models", {})

    @property
    def effect_models(self):
        return self.artifact.get("effect_models", {})

    @property
    def baseline_feature_cols(self):
        return self.artifact.get("baseline_feature_cols", [])

    @property
    def promo_feature_cols(self):
        return self.artifact.get("promo_feature_cols", [])

    @property
    def signal_cols(self):
        return self.artifact.get("signal_cols", [])

    @property
    def target_year(self):
        return int(self.artifact.get("TARGET_YEAR", 2025))


_opt_cache: Optional[OptimizeBundleAdapter] = None
_opt_mtime: Optional[float] = None
_opt_path: Optional[Path] = None


@dataclass
class MarketBundleAdapter:
    model: Any
    encoder: Any
    features: List[str]
    metadata: Dict[str, Any]

    def predict(self, X):
        return self.model.predict(X)

    def supported_horizons(self) -> List[int]:
        return [3, 4, 5, 6]


_market_cache: Optional[MarketBundleAdapter] = None
_market_mtime: Optional[float] = None
_market_path: Optional[Path] = None


class ModelRegistryService:
    def __init__(self, registry_path: Path, model_dir: Path):
        self.registry_path = registry_path
        self.model_dir = model_dir
        self._cache: Optional[Dict[str, Any]] = None
        self._mtime: Optional[float] = None

    def load_registry(self) -> Dict[str, Any]:
        if not self.registry_path.exists():
            return {"models": []}

        mtime = self.registry_path.stat().st_mtime
        if self._cache is not None and self._mtime == mtime:
            return self._cache

        data = json.loads(self.registry_path.read_text(encoding="utf-8"))
        if "models" not in data:
            data["models"] = []
        self._cache = data
        self._mtime = mtime
        return data

    def list_models(self) -> Tuple[List[Dict[str, Any]], List[str]]:
        registry = self.load_registry()
        models = registry.get("models", [])
        warnings = self._validate_models(models)
        return models, warnings

    def get_model(self, model_id: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        registry = self.load_registry()
        models = registry.get("models", [])
        for m in models:
            if m.get("id") == model_id:
                warnings = self._validate_models([m])
                return m, warnings
        return None, [f"model_id '{model_id}' not found in registry"]

    def get_metrics(self, model_id: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        model, warnings = self.get_model(model_id)
        if not model:
            return [], warnings
        metrics = model.get("metrics") or []
        if not metrics:
            warnings.append("metrics not available")
        return metrics, warnings

    def get_versions(self, model_id: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        model, warnings = self.get_model(model_id)
        if not model:
            return [], warnings
        versions = model.get("versions") or []
        if not versions:
            warnings.append("versions not available")
        return versions, warnings

    def get_explainability(self, model_id: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        model, warnings = self.get_model(model_id)
        if not model:
            return [], warnings
        explain = model.get("explainability") or []
        if not explain:
            warnings.append("explainability not available")
        return explain, warnings

    def _validate_models(self, models: List[Dict[str, Any]]) -> List[str]:
        warnings: List[str] = []
        for m in models:
            bundle = m.get("bundle_filename")
            if bundle:
                bundle_path = self.model_dir / bundle
                if not bundle_path.exists():
                    warnings.append(f"bundle missing: {bundle}")
            else:
                warnings.append(f"bundle_filename missing for model '{m.get('id')}'")
        return warnings


@dataclass
class ForecastBundleAdapter:
    model: Any
    feature_cols: List[str]
    cat_cols: List[str]
    ensemble: Dict[str, Any]
    metadata: Dict[str, Any]

    def predict(self, X):
        return self.model.predict(X)

    def predict_quantiles(self, X):
        return None

    def global_importance(self) -> Optional[List[Dict[str, float]]]:
        if hasattr(self.model, "feature_importances_"):
            importances = getattr(self.model, "feature_importances_")
            if importances is None:
                return None
            pairs = list(zip(self.feature_cols, np.asarray(importances, dtype=float)))
            pairs = sorted(pairs, key=lambda x: x[1], reverse=True)
            return [{"feature": f, "importance": float(v)} for f, v in pairs]
        return None

    def get_ensemble_weights(self) -> Tuple[float, float]:
        w_model = float(self.ensemble.get("w_model", 1.0))
        w_naive = float(self.ensemble.get("w_naive", 0.0))
        return w_model, w_naive


def load_forecast_bundle(model_dir: Path, registry: ModelRegistryService) -> ForecastBundleAdapter:
    registry_data, _ = registry.list_models()
    meta = next((m for m in registry_data if m.get("name") == "Demand Forecast" or m.get("id") == "demand_forecast_prod"), None)
    bundle_filename = None
    if meta:
        bundle_filename = meta.get("bundle_filename")

    bundle_path = model_dir / (bundle_filename or "demand_forecasting_model_bundle.joblib")
    global _forecast_cache, _forecast_mtime, _forecast_path
    if not bundle_path.exists():
        raise FileNotFoundError(f"Forecast bundle not found at {bundle_path}")

    mtime = bundle_path.stat().st_mtime
    if _forecast_cache is not None and _forecast_mtime == mtime and _forecast_path == bundle_path:
        return _forecast_cache

    bundle = joblib.load(bundle_path)
    if not isinstance(bundle, dict):
        raise ValueError("Forecast bundle must be a dict")

    model = bundle.get("model")
    feature_cols = bundle.get("feature_cols") or bundle.get("feature_columns") or []
    cat_cols = bundle.get("cat_cols") or []
    ensemble = bundle.get("ensemble") or {}

    if model is None or not feature_cols:
        raise ValueError("Forecast bundle missing required keys: model, feature_cols")

    metadata = meta or {"id": "demand_forecast_prod", "version": "v1"}

    adapter = ForecastBundleAdapter(
        model=model,
        feature_cols=list(feature_cols),
        cat_cols=list(cat_cols),
        ensemble=dict(ensemble),
        metadata=metadata,
    )
    _forecast_cache = adapter
    _forecast_mtime = mtime
    _forecast_path = bundle_path
    return adapter


def load_anomaly_bundle(model_dir: Path, registry: ModelRegistryService) -> AnomalyBundleAdapter:
    global _anomaly_cache, _anomaly_mtime, _anomaly_path
    registry_data, _ = registry.list_models()
    meta = next((m for m in registry_data if m.get("name") == "Anomaly Detection" or m.get("id") == "anomaly_detection_prod"), None)
    bundle_filename = None
    if meta:
        bundle_filename = meta.get("bundle_filename")

    bundle_path = model_dir / (bundle_filename or "anomaly_model_bundle.joblib")
    if not bundle_path.exists():
        raise FileNotFoundError(f"Anomaly bundle not found at {bundle_path}")

    mtime = bundle_path.stat().st_mtime
    if _anomaly_cache is not None and _anomaly_mtime == mtime and _anomaly_path == bundle_path:
        return _anomaly_cache

    bundle = joblib.load(bundle_path)
    if not isinstance(bundle, dict):
        raise ValueError("Anomaly bundle must be a dict")

    config = bundle.get("config") or {}
    metadata = meta or {"id": "anomaly_detection_prod", "version": "v1"}

    adapter = AnomalyBundleAdapter(config=config, metadata=metadata)
    _anomaly_cache = adapter
    _anomaly_mtime = mtime
    _anomaly_path = bundle_path
    return adapter


def load_optimize_bundle(model_dir: Path, registry: ModelRegistryService) -> OptimizeBundleAdapter:
    global _opt_cache, _opt_mtime, _opt_path
    registry_data, _ = registry.list_models()
    meta = next((m for m in registry_data if m.get("name") == "Promotion Optimization" or m.get("id") == "promotion_optimization_prod"), None)
    bundle_filename = None
    if meta:
        bundle_filename = meta.get("bundle_filename")

    bundle_path = model_dir / (bundle_filename or "event_impact_optimization_models.joblib")
    if not bundle_path.exists():
        raise FileNotFoundError(f"Optimization bundle not found at {bundle_path}")
    mtime = bundle_path.stat().st_mtime
    if _opt_cache is not None and _opt_mtime == mtime and _opt_path == bundle_path:
        return _opt_cache

    artifact = joblib.load(bundle_path)
    if not isinstance(artifact, dict):
        raise ValueError("Optimization bundle must be a dict")
    metadata = meta or {"id": "promotion_optimization_prod", "version": "v1"}
    adapter = OptimizeBundleAdapter(artifact=artifact, metadata=metadata)
    _opt_cache = adapter
    _opt_mtime = mtime
    _opt_path = bundle_path
    return adapter


def load_market_bundle(model_dir: Path, registry: ModelRegistryService) -> MarketBundleAdapter:
    global _market_cache, _market_mtime, _market_path
    registry_data, _ = registry.list_models()
    meta = next((m for m in registry_data if m.get("name") == "Market Share Intelligence" or m.get("id") == "market_share_intel_prod"), None)
    bundle_filename = None
    if meta:
        bundle_filename = meta.get("bundle_filename")

    bundle_path = model_dir / (bundle_filename or "marketshare_nlp_model_bundle.joblib")
    if not bundle_path.exists():
        raise FileNotFoundError(f"Market bundle not found at {bundle_path}")
    mtime = bundle_path.stat().st_mtime
    if _market_cache is not None and _market_mtime == mtime and _market_path == bundle_path:
        return _market_cache

    bundle = joblib.load(bundle_path)
    if not isinstance(bundle, dict):
        raise ValueError("Market bundle must be a dict")

    model = bundle.get("model")
    encoder = bundle.get("encoder")
    features = bundle.get("features") or []
    if model is None or not features:
        raise ValueError("Market bundle missing required keys: model, features")

    metadata = meta or {"id": "market_share_intel_prod", "version": "v1"}
    adapter = MarketBundleAdapter(model=model, encoder=encoder, features=list(features), metadata=metadata)
    _market_cache = adapter
    _market_mtime = mtime
    _market_path = bundle_path
    return adapter
