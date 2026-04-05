from __future__ import annotations

import json
from pathlib import Path

from backend.app.core.config import get_settings
from backend.app.services.data.repository import DataRepository
from backend.app.services.bundles.loader import ModelRegistryService
from backend.app.services.inference.forecast_service import ForecastService


def main() -> None:
    settings = get_settings()
    backend_dir = Path(__file__).resolve().parents[1]
    registry = ModelRegistryService(
        registry_path=backend_dir / "models" / "model_registry.json",
        model_dir=settings.MODEL_DIR,
    )
    repo = DataRepository(settings.DATA_DIR)

    service = ForecastService(repo=repo, settings=settings, registry=registry)
    opts = service.get_options()
    product_id = opts["products"][0]
    aps = opts["aps_list"][0]

    data, _ = service.predict(
        product_id=product_id,
        aps=aps,
        horizon_months=3,
        cutoff_date=None,
        scenarios={"temperature_pct": 5, "housing_growth_pct": -2},
        include_actuals=True,
        include_explain=False,
    )
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
