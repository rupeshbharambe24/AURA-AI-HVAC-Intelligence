from __future__ import annotations

import json
from pathlib import Path

from backend.app.core.config import get_settings
from backend.app.services.bundles.loader import ModelRegistryService
from backend.app.services.data.repository import DataRepository
from backend.app.services.inference.anomaly_service import AnomalyService


def main() -> None:
    settings = get_settings()
    backend_dir = Path(__file__).resolve().parents[1]
    registry = ModelRegistryService(
        registry_path=backend_dir / "models" / "model_registry.json",
        model_dir=settings.MODEL_DIR,
    )
    repo = DataRepository(settings.DATA_DIR)

    service = AnomalyService(repo=repo, settings=settings, registry=registry)
    opts = service.get_options()
    product_id = opts["products"][0]
    aps = opts["aps_list"][0]

    data, _ = service.detect(
        product_id=product_id,
        aps=aps,
        date_range=["2024-01-01", "2024-12-01"],
        thresholds=None,
        threshold=3.0,
        include_explanations=True,
    )
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
