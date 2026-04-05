from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from ...core.config import Settings
from ..bundles.loader import ModelRegistryService, OptimizeBundleAdapter, load_optimize_bundle
from ..data.repository import DataRepository


class OptimizeService:
    def __init__(self, repo: DataRepository, settings: Settings, registry: ModelRegistryService):
        self.repo = repo
        self.settings = settings
        self.registry = registry

    def optimize(
        self,
        constraints: Dict[str, Any],
        candidate_promos: List[Dict[str, Any]],
        products: List[str],
    ) -> Tuple[Dict[str, Any], List[str]]:
        warnings: List[str] = []
        bundle = load_optimize_bundle(self.settings.MODEL_DIR, self.registry)

        target_year = int(constraints.get("target_year", bundle.target_year))
        max_promos = int(constraints.get("max_promos_per_year", 3))
        exclude_months = set(int(m) for m in constraints.get("exclude_months", []))

        if not products:
            products = self.repo.get_products()

        baseline = _baseline_demand(self.repo, bundle, products, target_year, warnings)
        effects = _promo_effects(self.repo, bundle, candidate_promos, products, target_year)

        candidates = _generate_candidates(products, candidate_promos, exclude_months)
        try:
            unit_econ = self.repo.load_unit_economics()
        except FileNotFoundError:
            unit_econ = pd.DataFrame(columns=["product_id"])
            warnings.append("unit_economics.csv missing; profit uplift approximated as zero")

        scored = _score_candidates(candidates, baseline, effects, unit_econ)
        scored = sorted(scored, key=lambda r: r.get("expected_profit_uplift", 0), reverse=True)

        schedule = []
        for c in scored:
            if len(schedule) >= max_promos:
                break
            if c["month"] in exclude_months:
                continue
            schedule.append(c)

        try:
            capacity = self.repo.load_capacity_constraints()
        except FileNotFoundError:
            capacity = pd.DataFrame(columns=["product_id", "month_num", "capacity"])
            warnings.append("capacity_constraints.csv missing; capacity checks skipped")

        baseline_sim = _simulate_schedule([], baseline, effects, capacity, unit_econ)
        result = _simulate_schedule(schedule, baseline, effects, capacity, unit_econ)
        summary, promo_calendar, constraint_report = _summarize(
            schedule, baseline_sim, result, constraints
        )

        response = {
            "summary": summary,
            "promo_calendar": promo_calendar,
            "schedule": schedule,
            "constraint_report": constraint_report,
            "warnings": warnings,
        }
        return response, warnings


def _baseline_demand(
    repo: DataRepository,
    bundle: OptimizeBundleAdapter,
    products: List[str],
    year: int,
    warnings: List[str],
) -> pd.DataFrame:
    demand = repo.load_demand_long()
    ext = repo.load_external_signals()
    ext["month_num"] = ext["date"].dt.month
    ext["year"] = ext["date"].dt.year
    ext = ext[ext["year"] == year]

    rows = []
    for product in products:
        if product not in bundle.baseline_models:
            # fallback: last year average
            hist = demand[(demand["product_id"] == product) & (demand["date"].dt.year == year - 1)]
            avg = float(hist["demand"].mean()) if not hist.empty else 0.0
            for m in range(1, 13):
                rows.append({"product_id": product, "year": year, "month": m, "baseline_mean": avg, "baseline_std": 0.0})
            warnings.append(f"baseline model missing for {product}; using last-year average")
            continue

        model = bundle.baseline_models[product]
        for m in range(1, 13):
            sig = ext[ext["month_num"] == m].iloc[0].to_dict() if not ext[ext["month_num"] == m].empty else {}
            row = {"year": year, "month": m}
            row["month_sin"] = np.sin(2 * np.pi * m / 12.0)
            row["month_cos"] = np.cos(2 * np.pi * m / 12.0)
            for c in bundle.signal_cols:
                row[c] = sig.get(c, np.nan)
            X = pd.DataFrame([row], columns=bundle.baseline_feature_cols)
            yhat = float(model.predict(X)[0])
            rows.append({"product_id": product, "year": year, "month": m, "baseline_mean": max(yhat, 0.0), "baseline_std": 0.0})

    return pd.DataFrame(rows)


def _promo_effects(repo: DataRepository, bundle: OptimizeBundleAdapter, templates: List[Dict[str, Any]], products: List[str], year: int) -> pd.DataFrame:
    ext = repo.load_external_signals()
    ext["month_num"] = ext["date"].dt.month
    ext["year"] = ext["date"].dt.year
    ext = ext[ext["year"] == year]

    effect_rows = []
    for product in products:
        for m in range(1, 13):
            sig = ext[ext["month_num"] == m].iloc[0].to_dict() if not ext[ext["month_num"] == m].empty else {}
            for t in templates:
                promo_type = t.get("type", "discount")
                discount_pct = float(t.get("discount_pct", t.get("discount", 0.0)))
                duration_days = int(float(t.get("duration_weeks", 3)) * 7)
                row = {
                    "product": product,
                    "promo_type": promo_type,
                    "discount_pct": discount_pct,
                    "duration_days": duration_days,
                    "month_num": m,
                }
                for c in bundle.signal_cols:
                    row[c] = sig.get(c, np.nan)
                X = pd.DataFrame([row], columns=bundle.promo_feature_cols)
                preds = {}
                for tgt, model in bundle.effect_models.items():
                    preds[tgt] = float(model.predict(X)[0])
                effect_rows.append({
                    "product_id": product,
                    "month": m,
                    "promo_type": promo_type,
                    "discount_pct": discount_pct,
                    "duration_days": duration_days,
                    "lift_pct": float(np.clip(preds.get("lift_pct", 0.0), -10, 60)),
                    "prebuy_pct": float(np.clip(preds.get("prebuy_pct", 0.0), 0, 30)),
                    "postbuy_pct": float(np.clip(preds.get("postbuy_pct", 0.0), 0, 30)),
                    "margin_impact_pct": float(np.clip(preds.get("margin_impact_pct", 0.0), -30, 10)),
                })
    return pd.DataFrame(effect_rows)


def _generate_candidates(products: List[str], templates: List[Dict[str, Any]], exclude_months: set[int]) -> List[Dict[str, Any]]:
    candidates = []
    for product in products:
        for m in range(1, 13):
            if m in exclude_months:
                continue
            for t in templates:
                candidates.append({
                    "product_id": product,
                    "month": m,
                    "promo_type": t.get("type", "discount"),
                    "discount_pct": float(t.get("discount_pct", t.get("discount", 0.0))),
                    "duration_days": int(float(t.get("duration_weeks", 3)) * 7),
                })
    return candidates


def _score_candidates(
    candidates: List[Dict[str, Any]],
    baseline: pd.DataFrame,
    effects: pd.DataFrame,
    unit_econ: pd.DataFrame,
):
    out = []
    for c in candidates:
        base = baseline[(baseline["product_id"] == c["product_id"]) & (baseline["month"] == c["month"])]
        eff = effects[
            (effects["product_id"] == c["product_id"]) &
            (effects["month"] == c["month"]) &
            (effects["promo_type"] == c["promo_type"]) &
            (effects["discount_pct"] == c["discount_pct"]) &
            (effects["duration_days"] == c["duration_days"])
        ]
        if base.empty or eff.empty:
            continue
        base_demand = float(base.iloc[0]["baseline_mean"])
        lift = float(eff.iloc[0]["lift_pct"])
        expected_units = base_demand * (1.0 + lift / 100.0)
        econ = unit_econ[unit_econ["product_id"] == c["product_id"]]
        if not econ.empty:
            asp = float(econ.iloc[0].get("avg_selling_price", 0))
            gm_pct = float(econ.iloc[0].get("gross_margin_pct", 0))
            gp_unit = asp * gm_pct / 100.0
        else:
            gp_unit = 0.0
        expected_profit_uplift = (expected_units - base_demand) * gp_unit
        row = dict(c)
        row["expected_lift_pct"] = lift
        row["expected_profit_uplift"] = float(expected_profit_uplift)
        out.append(row)
    return out


def _simulate_schedule(
    schedule: List[Dict[str, Any]],
    baseline: pd.DataFrame,
    effects: pd.DataFrame,
    capacity: pd.DataFrame,
    unit_econ: pd.DataFrame,
) -> pd.DataFrame:
    sim = baseline.copy()
    sim["demand_raw"] = sim["baseline_mean"].astype(float)

    for ev in schedule:
        eff = effects[
            (effects["product_id"] == ev["product_id"]) &
            (effects["month"] == ev["month"]) &
            (effects["promo_type"] == ev["promo_type"]) &
            (effects["discount_pct"] == ev["discount_pct"]) &
            (effects["duration_days"] == ev["duration_days"])
        ]
        if eff.empty:
            continue
        e = eff.iloc[0]
        base0 = sim.loc[(sim["product_id"] == ev["product_id"]) & (sim["month"] == ev["month"]), "demand_raw"].iloc[0]
        sim.loc[(sim["product_id"] == ev["product_id"]) & (sim["month"] == ev["month"]), "demand_raw"] = base0 * (1.0 + float(e["lift_pct"]) / 100.0)

        pre_units = base0 * (float(e["prebuy_pct"]) / 100.0)
        post_units = base0 * (float(e["postbuy_pct"]) / 100.0)
        for lag, w in zip([1, 2], [0.6, 0.4]):
            m = ev["month"] - lag
            if 1 <= m <= 12:
                idx = (sim["product_id"] == ev["product_id"]) & (sim["month"] == m)
                sim.loc[idx, "demand_raw"] = np.maximum(sim.loc[idx, "demand_raw"] - pre_units * w, 0.0)
        for lag, w in zip([1, 2], [0.6, 0.4]):
            m = ev["month"] + lag
            if 1 <= m <= 12:
                idx = (sim["product_id"] == ev["product_id"]) & (sim["month"] == m)
                sim.loc[idx, "demand_raw"] = np.maximum(sim.loc[idx, "demand_raw"] - post_units * w, 0.0)

    cap = capacity.rename(columns={"capacity_units": "capacity"}).copy()
    if not cap.empty:
        sim = sim.merge(
            cap[["product_id", "month_num", "capacity"]],
            left_on=["product_id", "month"],
            right_on=["product_id", "month_num"],
            how="left",
        )
        sim["capacity"] = sim["capacity"].fillna(np.inf)
    else:
        sim["capacity"] = np.inf
    sim["final_demand"] = np.minimum(sim["demand_raw"], sim["capacity"])
    sim["lost_sales"] = np.maximum(sim["demand_raw"] - sim["capacity"], 0.0)

    ue = unit_econ.set_index("product_id") if not unit_econ.empty else pd.DataFrame()
    profits = []
    for _, r in sim.iterrows():
        p = r["product_id"]
        units = float(r["final_demand"])
        if not ue.empty and p in ue.index:
            asp = float(ue.loc[p].get("avg_selling_price", 0))
            gm_pct = float(ue.loc[p].get("gross_margin_pct", 0))
            gp_unit = asp * gm_pct / 100.0
        else:
            gp_unit = 0.0
        profits.append(units * gp_unit)
    sim["gross_profit"] = profits
    return sim


def _summarize(
    schedule: List[Dict[str, Any]],
    baseline_sim: pd.DataFrame,
    sim: pd.DataFrame,
    constraints: Dict[str, Any],
):
    baseline_profit = float(baseline_sim["gross_profit"].sum())
    optimized_profit = float(sim["gross_profit"].sum())

    profit_improvement_pct = 0.0
    if baseline_profit > 0:
        profit_improvement_pct = (optimized_profit / baseline_profit - 1.0) * 100.0

    total_capacity = float(sim["capacity"].replace(np.inf, 0).sum())
    total_final = float(sim["final_demand"].sum())
    capacity_utilization = (total_final / total_capacity * 100.0) if total_capacity > 0 else 0.0
    lost_sales_pct = float(sim["lost_sales"].sum() / max(total_final, 1.0) * 100.0)
    volatility_metric = float(sim.groupby("month")["final_demand"].sum().var())

    summary = {
        "baseline_profit_mean": baseline_profit,
        "optimized_profit_mean": optimized_profit,
        "profit_improvement_pct": profit_improvement_pct,
        "capacity_utilization_pct": capacity_utilization,
        "lost_sales_pct": lost_sales_pct,
        "volatility_metric": volatility_metric,
        "violations": 0,
    }

    promo_calendar = []
    for m in range(1, 13):
        month_sched = [s for s in schedule if s["month"] == m]
        if not month_sched:
            continue
        avg_lift = float(np.mean([s.get("expected_lift_pct", 0.0) for s in month_sched]))
        budget = 0.0
        promo_calendar.append({
            "month": f"{constraints.get('target_year', 2025)}-{m:02d}",
            "promos": len(month_sched),
            "expected_lift_pct": avg_lift,
            "budget": budget,
        })

    details: List[str] = []
    max_promos = int(constraints.get("max_promos_per_year", 3))
    exclude_months = set(int(m) for m in constraints.get("exclude_months", []))
    max_promos_ok = len(schedule) <= max_promos
    if not max_promos_ok:
        details.append("Exceeded max_promos_per_year")

    exclude_months_ok = not any(s["month"] in exclude_months for s in schedule)
    if not exclude_months_ok:
        details.append("Schedule includes excluded months")

    capacity_limit = constraints.get("capacity_limit_pct")
    capacity_ok = True
    if capacity_limit is not None:
        capacity_ok = lost_sales_pct <= float(capacity_limit)
        if not capacity_ok:
            details.append("Capacity limit exceeded")

    variance_ratio = constraints.get("variance_limit_ratio")
    variance_ok = True
    if variance_ratio is not None:
        baseline_var = float(baseline_sim.groupby("month")["final_demand"].sum().var())
        if baseline_var > 0:
            variance_ok = volatility_metric <= baseline_var * float(variance_ratio)
            if not variance_ok:
                details.append("Variance limit exceeded")

    min_uplift = constraints.get("min_mean_uplift_pct")
    chance_ok = True
    if min_uplift is not None:
        chance_ok = profit_improvement_pct >= float(min_uplift)
        if not chance_ok:
            details.append("Minimum uplift target not met")

    constraint_report = {
        "max_promos_ok": max_promos_ok,
        "exclude_months_ok": exclude_months_ok,
        "capacity_ok": capacity_ok,
        "variance_ok": variance_ok,
        "chance_ok": chance_ok,
        "details": details,
    }
    summary["violations"] = len(details)
    return summary, promo_calendar, constraint_report
