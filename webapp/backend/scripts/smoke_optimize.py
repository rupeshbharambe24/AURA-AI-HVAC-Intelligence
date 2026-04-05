from __future__ import annotations

import json
import os
import time
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
    payload = {
        "constraints": {
            "max_promos_per_year": 2,
            "exclude_months": [7, 8],
            "capacity_limit_pct": 10.0,
            "variance_limit_ratio": 2.0,
            "chance_level": 0.5,
            "min_mean_uplift_pct": 1.0,
            "target_year": 2025,
        },
        "candidate_promos": [
            {"type": "discount", "discount_pct": 0.15, "duration_weeks": 3}
        ],
        "products": ["AH", "CL"],
    }

    submit = _post("/api/v1/optimize/submit", payload)
    job_id = submit.get("job_id")
    if not job_id:
        raise SystemExit(f"No job_id returned: {submit}")

    for _ in range(60):
        time.sleep(1)
        status = _get(f"/api/v1/jobs/{job_id}")
        if status.get("status") in ("completed", "failed"):
            print(json.dumps(status, indent=2))
            return

    raise SystemExit("Timed out waiting for optimization job")


if __name__ == "__main__":
    main()
