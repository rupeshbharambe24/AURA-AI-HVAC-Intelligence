from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run backend, frontend, or both.")
    parser.add_argument("--backend", action="store_true", help="Run backend only")
    parser.add_argument("--frontend", action="store_true", help="Run frontend only")
    parser.add_argument("--all", action="store_true", help="Run both backend and frontend")
    return parser.parse_args()


def _start_process(cmd: list[str], cwd: Path, name: str) -> subprocess.Popen:
    print(f"Starting {name}: {' '.join(cmd)}")
    return subprocess.Popen(cmd, cwd=str(cwd))


def _stop_process(proc: subprocess.Popen, name: str) -> None:
    if proc.poll() is not None:
        return
    print(f"Stopping {name}...")
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


def main() -> int:
    root = Path(__file__).resolve().parent
    args = parse_args()

    run_backend = args.backend or args.all or (not args.frontend and not args.backend)
    run_frontend = args.frontend or args.all or (not args.frontend and not args.backend)

    procs: list[tuple[str, subprocess.Popen]] = []

    if run_backend:
        procs.append((
            "backend",
            _start_process([sys.executable, "run_backend.py"], root, "backend"),
        ))

    if run_frontend:
        procs.append((
            "frontend",
            _start_process([sys.executable, "run_frontend.py"], root, "frontend"),
        ))

    if not procs:
        print("Nothing to run. Use --backend, --frontend, or --all.")
        return 1

    try:
        while True:
            time.sleep(1)
            for name, proc in procs:
                if proc.poll() is not None:
                    print(f"{name} exited with code {proc.returncode}")
                    return proc.returncode or 0
    except KeyboardInterrupt:
        pass
    finally:
        for name, proc in procs:
            _stop_process(proc, name)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
