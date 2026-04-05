from __future__ import annotations

import json
import os
import urllib.request


BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


def _post(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get(path: str) -> dict:
    with urllib.request.urlopen(f"{BASE_URL}{path}") as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    options = _get("/api/v1/market-share/options")
    products = options.get("products", [])
    if not products:
        raise SystemExit("No products returned")

    payload = {
        "product_id": products[0],
        "horizon_months": 3,
        "as_of_date": options.get("default_as_of_date"),
        "news_filters": {"regulation": True, "pricing": True},
    }

    result = _post("/api/v1/market-share/predict", payload)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
