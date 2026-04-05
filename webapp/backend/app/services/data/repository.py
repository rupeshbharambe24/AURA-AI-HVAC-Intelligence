from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, Sequence

import pandas as pd


class DataRepository:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self._demand_cache: Optional[pd.DataFrame] = None
        self._demand_mtime: Optional[float] = None
        self._external_cache: Optional[pd.DataFrame] = None
        self._external_mtime: Optional[float] = None
        self._promo_cache: Optional[pd.DataFrame] = None
        self._promo_mtime: Optional[float] = None
        self._capacity_cache: Optional[pd.DataFrame] = None
        self._capacity_mtime: Optional[float] = None
        self._unit_cache: Optional[pd.DataFrame] = None
        self._unit_mtime: Optional[float] = None
        self._market_cache: Optional[pd.DataFrame] = None
        self._market_mtime: Optional[float] = None
        self._reg_cache: Optional[pd.DataFrame] = None
        self._reg_mtime: Optional[float] = None
        self._news_cache: Optional[dict] = None
        self._news_mtime: Optional[float] = None
        self._news_df_cache: Optional[pd.DataFrame] = None
        self._news_df_mtime: Optional[float] = None

    def exists(self) -> bool:
        return self.data_dir.exists()

    def list_files(self) -> list[str]:
        if not self.data_dir.exists():
            return []
        return [p.name for p in self.data_dir.iterdir() if p.is_file()]

    def list_datasets(self) -> list[Path]:
        if not self.data_dir.exists():
            return []
        return sorted(
            [p for p in self.data_dir.iterdir() if p.is_file() and p.suffix.lower() in {".csv", ".json"}],
            key=lambda p: p.name.lower(),
        )

    def load_dataset_df(self, name: str) -> pd.DataFrame:
        path = self.data_dir / name
        if not path.exists():
            raise FileNotFoundError(f"dataset '{name}' not found in {self.data_dir}")
        if path.suffix.lower() == ".csv":
            return pd.read_csv(path)
        if path.suffix.lower() == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return pd.DataFrame(data)
            if isinstance(data, dict):
                if "articles" in data and isinstance(data["articles"], list):
                    return pd.DataFrame(data["articles"])
                return pd.DataFrame([data])
        raise ValueError(f"Unsupported dataset format: {path.suffix}")

    def get_dataset_rows(self, name: str, limit: int = 200) -> list[dict]:
        df = self.load_dataset_df(name)
        if df.empty:
            return []
        return df.head(limit).to_dict(orient="records")

    def get_dataset_timeseries(self, name: str, metric: Optional[str] = None, limit: int = 200) -> list[dict]:
        df = self.load_dataset_df(name)
        if df.empty:
            return []

        work = df.copy()
        if "date" in work.columns:
            work["date"] = pd.to_datetime(work["date"], errors="coerce")
        elif {"year", "month"}.issubset(work.columns):
            work["date"] = pd.to_datetime(work[["year"]].assign(month=work["month"], day=1), errors="coerce")
        elif {"year", "month_num"}.issubset(work.columns):
            work["date"] = pd.to_datetime(work[["year"]].assign(month=work["month_num"], day=1), errors="coerce")
        else:
            return []

        work = work.dropna(subset=["date"]).sort_values("date")
        numeric_cols = work.select_dtypes(include=["number"]).columns.tolist()
        numeric_cols = [c for c in numeric_cols if c not in {"year", "month", "month_num"}]
        if not metric:
            metric = numeric_cols[0] if numeric_cols else None
        if not metric or metric not in work.columns:
            return []

        series = work[["date", metric]].dropna().head(limit)
        return [{"date": d.strftime("%Y-%m-%d"), "value": float(v)} for d, v in zip(series["date"], series[metric])]

    def load_demand_long(self) -> pd.DataFrame:
        path = self.data_dir / "demand_history.csv"
        if not path.exists():
            raise FileNotFoundError(f"demand_history.csv not found in {self.data_dir}")

        mtime = path.stat().st_mtime
        if self._demand_cache is not None and self._demand_mtime == mtime:
            return self._demand_cache.copy()

        df_wide = pd.read_csv(path)
        months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        month_map = {m: i + 1 for i, m in enumerate(months)}

        month_cols = [c for c in df_wide.columns if c in months]
        id_cols = [c for c in df_wide.columns if c not in month_cols]
        df_long = df_wide.melt(
            id_vars=id_cols,
            value_vars=month_cols,
            var_name="month",
            value_name="demand",
        )

        df_long["month_num"] = df_long["month"].map(month_map).astype(int)
        df_long["date"] = pd.to_datetime(
            df_long[["year"]].assign(month=df_long["month_num"], day=1)
        )
        df_long = df_long.rename(columns={"product": "product_id"})
        df_long["demand"] = pd.to_numeric(df_long["demand"], errors="coerce").fillna(0.0)
        df_long = df_long[["date", "year", "month_num", "product_id", "aps", "demand"]]
        df_long = df_long.sort_values(["product_id", "aps", "date"]).reset_index(drop=True)

        self._demand_cache = df_long
        self._demand_mtime = mtime
        return df_long.copy()

    def load_external_signals(self) -> pd.DataFrame:
        path = self.data_dir / "external_signals.csv"
        if not path.exists():
            raise FileNotFoundError(f"external_signals.csv not found in {self.data_dir}")

        mtime = path.stat().st_mtime
        if self._external_cache is not None and self._external_mtime == mtime:
            return self._external_cache.copy()

        ext = pd.read_csv(path)
        if "date" in ext.columns:
            ext["date"] = pd.to_datetime(ext["date"])
        elif {"year", "month"}.issubset(ext.columns):
            ext["date"] = pd.to_datetime(ext[["year"]].assign(month=ext["month"], day=1))
        elif {"year", "month_num"}.issubset(ext.columns):
            ext["date"] = pd.to_datetime(ext[["year"]].assign(month=ext["month_num"], day=1))
        else:
            raise ValueError("external_signals.csv must include date or (year, month)")

        ext["date"] = ext["date"].dt.to_period("M").dt.to_timestamp()
        ext = ext.sort_values("date").reset_index(drop=True)

        self._external_cache = ext
        self._external_mtime = mtime
        return ext.copy()

    def get_products(self) -> list[str]:
        df = self.load_demand_long()
        return sorted(df["product_id"].dropna().unique().tolist())

    def get_aps_list(self, product_id: Optional[str] = None) -> list[str]:
        df = self.load_demand_long()
        if product_id:
            df = df[df["product_id"] == product_id]
        return sorted(df["aps"].dropna().unique().tolist())

    def get_series(self, product_id: str, aps: str) -> pd.DataFrame:
        df = self.load_demand_long()
        series = df[(df["product_id"] == product_id) & (df["aps"] == aps)].copy()
        if series.empty:
            raise ValueError(f"No demand series found for product_id={product_id}, aps={aps}")
        return series.sort_values("date").reset_index(drop=True)

    def get_latest_date(self, product_id: str, aps: str) -> pd.Timestamp:
        series = self.get_series(product_id, aps)
        return series["date"].max()

    def load_promotion_history(self) -> pd.DataFrame:
        path = self.data_dir / "promotion_history.csv"
        if not path.exists():
            raise FileNotFoundError(f"promotion_history.csv not found in {self.data_dir}")
        mtime = path.stat().st_mtime
        if self._promo_cache is not None and self._promo_mtime == mtime:
            return self._promo_cache.copy()

        promo = pd.read_csv(path)
        if "product" in promo.columns:
            promo = promo.rename(columns={"product": "product_id"})
        if "month" in promo.columns and promo["month"].dtype == object:
            month_map = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
            promo["month_num"] = promo["month"].map(month_map).astype(int)
        elif "month" in promo.columns:
            promo["month_num"] = promo["month"].astype(int)
        elif "month_num" in promo.columns:
            promo["month_num"] = promo["month_num"].astype(int)
        else:
            raise ValueError("promotion_history.csv missing month column")

        promo["date"] = pd.to_datetime(promo[["year"]].assign(month=promo["month_num"], day=1))
        if "aps" not in promo.columns:
            promo["aps"] = "ALL"
        promo = promo.sort_values(["product_id", "aps", "date"]).reset_index(drop=True)

        self._promo_cache = promo
        self._promo_mtime = mtime
        return promo.copy()

    def load_capacity_constraints(self) -> pd.DataFrame:
        path = self.data_dir / "capacity_constraints.csv"
        if not path.exists():
            raise FileNotFoundError(f"capacity_constraints.csv not found in {self.data_dir}")
        mtime = path.stat().st_mtime
        if self._capacity_cache is not None and self._capacity_mtime == mtime:
            return self._capacity_cache.copy()

        cap = pd.read_csv(path)
        if "product" in cap.columns:
            cap = cap.rename(columns={"product": "product_id"})
        if "month" in cap.columns and cap["month"].dtype == object:
            month_map = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
            cap["month_num"] = cap["month"].map(month_map).astype(int)
        elif "month" in cap.columns:
            cap["month_num"] = cap["month"].astype(int)
        elif "month_num" in cap.columns:
            cap["month_num"] = cap["month_num"].astype(int)
        else:
            raise ValueError("capacity_constraints.csv missing month column")

        cap["date"] = pd.to_datetime(cap[["year"]].assign(month=cap["month_num"], day=1))
        if "aps" not in cap.columns:
            cap["aps"] = "ALL"
        cap = cap.sort_values(["product_id", "aps", "date"]).reset_index(drop=True)

        self._capacity_cache = cap
        self._capacity_mtime = mtime
        return cap.copy()

    def get_promos(self, product_id: str, aps: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
        promo = self.load_promotion_history()
        df = promo[(promo["product_id"] == product_id) & (promo["date"].between(start, end))]
        if "aps" in df.columns:
            df = df[(df["aps"] == aps) | (df["aps"] == "ALL")]
        return df.reset_index(drop=True)

    def get_capacity(self, product_id: str, aps: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
        cap = self.load_capacity_constraints()
        df = cap[(cap["product_id"] == product_id) & (cap["date"].between(start, end))]
        if "aps" in df.columns:
            df = df[(df["aps"] == aps) | (df["aps"] == "ALL")]
        return df.reset_index(drop=True)

    def get_latest_cutoff_date(self) -> pd.Timestamp:
        df = self.load_demand_long()
        return df["date"].max()

    def load_unit_economics(self) -> pd.DataFrame:
        path = self.data_dir / "unit_economics.csv"
        if not path.exists():
            raise FileNotFoundError(f"unit_economics.csv not found in {self.data_dir}")
        mtime = path.stat().st_mtime
        if self._unit_cache is not None and self._unit_mtime == mtime:
            return self._unit_cache.copy()
        ue = pd.read_csv(path)
        if "product" in ue.columns:
            ue = ue.rename(columns={"product": "product_id"})
        self._unit_cache = ue
        self._unit_mtime = mtime
        return ue.copy()

    def get_unit_economics(self, product_id: str) -> dict:
        ue = self.load_unit_economics()
        row = ue[ue["product_id"] == product_id]
        if row.empty:
            return {}
        return row.iloc[0].to_dict()

    def load_market_share_history(self) -> pd.DataFrame:
        path = self.data_dir / "market_share_history.csv"
        if not path.exists():
            raise FileNotFoundError(f"market_share_history.csv not found in {self.data_dir}")
        mtime = path.stat().st_mtime
        if self._market_cache is not None and self._market_mtime == mtime:
            return self._market_cache.copy()

        df_wide = pd.read_csv(path)
        months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        month_map = {m: i + 1 for i, m in enumerate(months)}
        month_cols = [c for c in df_wide.columns if c in months]
        id_cols = [c for c in df_wide.columns if c not in month_cols]
        df_long = df_wide.melt(
            id_vars=id_cols,
            value_vars=month_cols,
            var_name="month",
            value_name="market_share",
        )
        df_long["month_num"] = df_long["month"].map(month_map).astype(int)
        df_long["date"] = pd.to_datetime(
            df_long[["year"]].assign(month=df_long["month_num"], day=1)
        )
        df_long = df_long.rename(columns={"product": "product_id"})
        df_long["market_share"] = pd.to_numeric(df_long["market_share"], errors="coerce").fillna(0.0)
        df_long = df_long.sort_values(["product_id", "date"]).reset_index(drop=True)
        self._market_cache = df_long
        self._market_mtime = mtime
        return df_long.copy()

    def get_market_share_series(self, product_id: str) -> pd.DataFrame:
        df = self.load_market_share_history()
        series = df[df["product_id"] == product_id].copy()
        if series.empty:
            raise ValueError(f"No market share series for product_id={product_id}")
        return series.sort_values("date").reset_index(drop=True)

    def load_regulatory_timeline(self) -> pd.DataFrame:
        path = self.data_dir / "regulatory_timeline.csv"
        if not path.exists():
            raise FileNotFoundError(f"regulatory_timeline.csv not found in {self.data_dir}")
        mtime = path.stat().st_mtime
        if self._reg_cache is not None and self._reg_mtime == mtime:
            return self._reg_cache.copy()
        reg = pd.read_csv(path)
        reg["announcement_date"] = pd.to_datetime(reg["announcement_date"])
        reg["effective_date"] = pd.to_datetime(reg["effective_date"])
        if "products_affected" in reg.columns:
            reg["products_list"] = reg["products_affected"].fillna("").apply(
                lambda v: [s.strip() for s in str(v).split(",") if s.strip()]
            )
        else:
            reg["products_list"] = [[] for _ in range(len(reg))]
        self._reg_cache = reg
        self._reg_mtime = mtime
        return reg.copy()

    def load_news_corpus(self) -> dict:
        path = self.data_dir / "news_corpus.json"
        if not path.exists():
            raise FileNotFoundError(f"news_corpus.json not found in {self.data_dir}")
        mtime = path.stat().st_mtime
        if self._news_cache is not None and self._news_mtime == mtime:
            return self._news_cache
        data = json.loads(path.read_text(encoding="utf-8"))
        self._news_cache = data
        self._news_mtime = mtime
        return data

    def load_news_dataframe(self) -> pd.DataFrame:
        path = self.data_dir / "news_corpus.json"
        if not path.exists():
            raise FileNotFoundError(f"news_corpus.json not found in {self.data_dir}")
        mtime = path.stat().st_mtime
        if self._news_df_cache is not None and self._news_df_mtime == mtime:
            return self._news_df_cache.copy()

        data = self.load_news_corpus()
        articles = data.get("articles", [])
        df = pd.DataFrame(articles)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        self._news_df_cache = df
        self._news_df_mtime = mtime
        return df.copy()

    def get_news_window(
        self,
        start: pd.Timestamp,
        end: pd.Timestamp,
        tags: Optional[Sequence[str]] = None,
    ) -> pd.DataFrame:
        df = self.load_news_dataframe()
        if df.empty:
            return df
        df = df[(df["date"] >= start) & (df["date"] <= end)].copy()
        if tags:
            tag_set = set(tags)

            def _has_tag(row_tags: List[str]) -> bool:
                if not isinstance(row_tags, list):
                    return False
                return any(t in tag_set for t in row_tags)

            df = df[df["tags"].apply(_has_tag)]
        return df.sort_values("date").reset_index(drop=True)

    def get_market_products(self) -> list[str]:
        df = self.load_market_share_history()
        return sorted(df["product_id"].dropna().unique().tolist())

    def get_market_share_latest_date(self) -> pd.Timestamp:
        df = self.load_market_share_history()
        return df["date"].max()

    def get_regulations_for_product(self, product_id: str) -> pd.DataFrame:
        reg = self.load_regulatory_timeline()
        if "products_list" not in reg.columns:
            return reg.head(0)
        mask = reg["products_list"].apply(lambda items: product_id in items)
        return reg[mask].reset_index(drop=True)
