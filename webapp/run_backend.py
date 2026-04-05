from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv


def main() -> int:
    root = Path(__file__).resolve().parent
    load_dotenv(root / ".env")
    load_dotenv(root / "backend" / ".env")
    env = os.environ.get("ENV", "dev").lower()
    host = os.environ.get("HOST", "0.0.0.0")
    port = os.environ.get("PORT", "8000")

    # Ensure the repo root is the first import location for "backend.*"
    os.environ["PYTHONPATH"] = str(root)

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.app.main:app",
        "--host",
        host,
        "--port",
        str(port),
        "--app-dir",
        str(root),
    ]
    if env == "dev":
        cmd.append("--reload")

    return subprocess.call(cmd, cwd=root)


if __name__ == "__main__":
    raise SystemExit(main())
