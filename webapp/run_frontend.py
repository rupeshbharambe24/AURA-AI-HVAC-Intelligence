from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent
    frontend_dir = root / "frontend"
    pkg_path = frontend_dir / "package.json"
    if not pkg_path.exists():
        print("package.json not found in frontend/")
        return 1

    scripts = json.loads(pkg_path.read_text(encoding="utf-8")).get("scripts", {})
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    if "dev" in scripts:
        # Force port 5173 to avoid clashing with backend (8000).
        cmd = [npm_cmd, "run", "dev", "--", "--port", "5173"]
    elif "start" in scripts:
        cmd = [npm_cmd, "start"]
    else:
        print("No dev/start script found in frontend/package.json")
        return 1

    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        install_cmd = [npm_cmd, "install"]
        code = subprocess.call(install_cmd, cwd=frontend_dir)
        if code != 0:
            return code

    return subprocess.call(cmd, cwd=frontend_dir)


if __name__ == "__main__":
    raise SystemExit(main())
