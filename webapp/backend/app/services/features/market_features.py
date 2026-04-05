from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from ..data.repository import DataRepository


TAG_FEATURES = [
    "capacity",
    "construction",
    "earnings",
    "energy",
    "housing",
    "market",
    "pricing",
    "product_launch",
    "regulation",
    "supply_chain",
    "technology",
]

SENTIMENT_MAP = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}

FILTER_TAG_MAP = {
    "competitor": ["market", "product_launch", "earnings"],
    "regulation": ["regulation"],
    "supply_chain": ["supply_chain", "capacity"],
    "pricing": ["pricing", "energy"],
}


def resolve_news_tags(news_filters: Optional[Dict[str, bool]]) -> Tuple[Optional[set[str]], List[str]]:
    warnings: List[str] = []
    if not news_filters or not any(news_filters.values()):
        return None, warnings

    tags: set[str] = set()
    for key, enabled in news_filters.items():
        if not enabled:
            continue
        mapped = FILTER_TAG_MAP.get(key)
        if mapped:
            tags.update(mapped)
            if key == "competitor":
                warnings.append("competitor filter mapped to market/product_launch/earnings tags")
        else:
            warnings.append(f"unknown news filter: {key}")
    return tags or None, warnings


def aggregate_news_features(news_df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> Dict[str, float]:
    if news_df.empty:
        base = {"news_volume": 0.0, "avg_sentiment": 0.0}
        base.update({t: 0.0 for t in TAG_FEATURES})
        return base

    window = news_df[(news_df["date"] >= start) & (news_df["date"] <= end)].copy()
    if window.empty:
        base = {"news_volume": 0.0, "avg_sentiment": 0.0}
        base.update({t: 0.0 for t in TAG_FEATURES})
        return base

    sentiment_scores = []
    weights = []
    tag_scores = {t: 0.0 for t in TAG_FEATURES}

    for _, row in window.iterrows():
        sentiment = SENTIMENT_MAP.get(str(row.get("sentiment", "neutral")).lower(), 0.0)
        weight = float(row.get("relevance_score", 1.0))
        sentiment_scores.append(sentiment * weight)
        weights.append(weight)
        tags = row.get("tags", [])
        if isinstance(tags, list):
            for tag in tags:
                if tag in tag_scores:
                    tag_scores[tag] += weight

    news_volume = float(len(window))
    avg_sentiment = float(np.sum(sentiment_scores) / max(np.sum(weights), 1.0))
    features = {"news_volume": news_volume, "avg_sentiment": avg_sentiment}
    features.update(tag_scores)
    return features


def build_regulatory_features(reg_df: pd.DataFrame, target_date: pd.Timestamp) -> Dict[str, float]:
    if reg_df.empty:
        return {
            "months_since_announcement": 0.0,
            "months_until_effective": 0.0,
            "reg_impact": 0.0,
            "reg_active": 0.0,
        }

    reg = reg_df.copy()
    reg["announcement_date"] = pd.to_datetime(reg["announcement_date"])
    reg["effective_date"] = pd.to_datetime(reg["effective_date"])
    if "compliance_deadline" in reg.columns:
        reg["compliance_deadline"] = pd.to_datetime(reg["compliance_deadline"], errors="coerce")

    def _months_between(a: pd.Timestamp, b: pd.Timestamp) -> int:
        return (a.year - b.year) * 12 + (a.month - b.month)

    past_ann = reg[reg["announcement_date"] <= target_date]
    if not past_ann.empty:
        ann_date = past_ann["announcement_date"].max()
        months_since = max(_months_between(target_date, ann_date), 0)
    else:
        months_since = 0

    future_eff = reg[reg["effective_date"] >= target_date]
    if not future_eff.empty:
        eff_date = future_eff["effective_date"].min()
        months_until = max(_months_between(eff_date, target_date), 0)
    else:
        months_until = 0

    if "compliance_deadline" in reg.columns:
        active = reg[(reg["effective_date"] <= target_date) & (reg["compliance_deadline"] >= target_date)]
    else:
        active = reg[reg["effective_date"] <= target_date]

    reg_active = 1.0 if not active.empty else 0.0

    impact_map = {"low": 0.1, "medium": 0.2, "high": 0.3}
    impact_values = []
    for _, row in reg.iterrows():
        impact_values.append(impact_map.get(str(row.get("impact_magnitude", "")).lower(), 0.0))
    reg_impact = float(max(impact_values) if impact_values else 0.0)

    return {
        "months_since_announcement": float(months_since),
        "months_until_effective": float(months_until),
        "reg_impact": reg_impact,
        "reg_active": reg_active,
    }


def build_external_lag_features(ext_df: pd.DataFrame, target_date: pd.Timestamp) -> Dict[str, float]:
    if ext_df.empty:
        return {
            "housing_starts_k_lag3": 0.0,
            "consumer_confidence_lag3": 0.0,
            "energy_price_idx_lag3": 0.0,
            "interest_rate_pct_lag3": 0.0,
        }

    ext = ext_df.copy()
    if "date" not in ext.columns:
        return {
            "housing_starts_k_lag3": 0.0,
            "consumer_confidence_lag3": 0.0,
            "energy_price_idx_lag3": 0.0,
            "interest_rate_pct_lag3": 0.0,
        }

    lag_date = (target_date - pd.DateOffset(months=3)).to_period("M").to_timestamp()
    row = ext[ext["date"] == lag_date]
    if row.empty:
        row = ext[ext["date"] <= target_date]
    if row.empty:
        row = ext.tail(1)

    row = row.iloc[0] if not row.empty else None
    if row is None:
        return {
            "housing_starts_k_lag3": 0.0,
            "consumer_confidence_lag3": 0.0,
            "energy_price_idx_lag3": 0.0,
            "interest_rate_pct_lag3": 0.0,
        }

    return {
        "housing_starts_k_lag3": float(row.get("housing_starts_k", 0.0)),
        "consumer_confidence_lag3": float(row.get("consumer_confidence", 0.0)),
        "energy_price_idx_lag3": float(row.get("energy_price_idx", 0.0)),
        "interest_rate_pct_lag3": float(row.get("interest_rate_pct", 0.0)),
    }


def encode_product(encoder: Optional[object], product_id: str) -> Tuple[float, List[str]]:
    warnings: List[str] = []
    if encoder is None:
        return 0.0, ["product encoder missing; using 0"]
    try:
        encoded = encoder.transform([product_id])[0]
        return float(encoded), warnings
    except Exception:
        warnings.append("product_id not in encoder; using 0")
        return 0.0, warnings


def build_market_feature_row(
    repo: DataRepository,
    product_id: str,
    target_date: pd.Timestamp,
    lag_values: Sequence[float],
    news_df: pd.DataFrame,
    ext_df: pd.DataFrame,
    reg_df: pd.DataFrame,
    encoder: Optional[object],
) -> Tuple[Dict[str, float], List[str]]:
    warnings: List[str] = []
    row: Dict[str, float] = {
        "year": float(target_date.year),
        "month_num": float(target_date.month),
    }

    for i in range(1, 7):
        val = lag_values[i - 1] if i - 1 < len(lag_values) else 0.0
        row[f"share_lag_{i}"] = float(val)

    news_start = (target_date - pd.DateOffset(months=2)).to_period("M").to_timestamp()
    news_end = target_date.to_period("M").to_timestamp()
    row.update(aggregate_news_features(news_df, news_start, news_end))
    row.update(build_external_lag_features(ext_df, target_date))
    row.update(build_regulatory_features(reg_df, target_date))

    encoded, enc_warn = encode_product(encoder, product_id)
    warnings.extend(enc_warn)
    row["product_encoded"] = encoded

    return row, warnings


def build_news_timeline(
    news_df: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    max_items: int = 200,
) -> List[Dict[str, object]]:
    if news_df.empty:
        return []
    window = news_df[(news_df["date"] >= start) & (news_df["date"] <= end)].copy()
    window = window.sort_values("date").head(max_items)
    timeline = []
    for _, row in window.iterrows():
        timeline.append(
            {
                "date": pd.to_datetime(row["date"]).strftime("%Y-%m-%d"),
                "headline": str(row.get("headline", "")),
                "sentiment": str(row.get("sentiment", "neutral")),
                "tags": list(row.get("tags", [])) if isinstance(row.get("tags", []), list) else [],
                "relevance": float(row.get("relevance_score", 0.0)),
            }
        )
    return timeline


def derive_tag_drivers(news_df: pd.DataFrame, max_items: int = 5) -> List[Dict[str, float]]:
    if news_df.empty:
        return []
    scores = {t: 0.0 for t in TAG_FEATURES}
    for _, row in news_df.iterrows():
        weight = float(row.get("relevance_score", 1.0))
        tags = row.get("tags", [])
        if isinstance(tags, list):
            for tag in tags:
                if tag in scores:
                    scores[tag] += weight
    total = sum(scores.values())
    if total <= 0:
        return []
    pairs = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:max_items]
    return [{"name": _tag_to_driver_name(k), "importance_pct": float(v / total * 100.0)} for k, v in pairs]


def _tag_to_driver_name(tag: str) -> str:
    mapping = {
        "capacity": "Capacity news",
        "construction": "Construction news",
        "earnings": "Earnings news",
        "energy": "Energy costs",
        "housing": "Housing market",
        "market": "Market competition",
        "pricing": "Pricing pressure",
        "product_launch": "Product launches",
        "regulation": "Regulatory news",
        "supply_chain": "Supply chain",
        "technology": "Technology shifts",
    }
    return mapping.get(tag, tag)
