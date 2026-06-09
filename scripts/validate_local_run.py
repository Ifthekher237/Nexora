"""Validate basic local Nexora run readiness."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.deployment import environment_review_service


def main() -> int:
    review = environment_review_service.review_environment(check_ollama=True)
    missing_configs = [item for item in review.get("config_files", []) if not item.get("exists")]
    missing_dirs = [item for item in review.get("required_directories", []) if not item.get("exists")]
    result = {
        "status": "ready" if not missing_configs and not missing_dirs and review.get("python_version_ok") else "needs_attention",
        "python_version": review.get("python_version"),
        "python_version_ok": review.get("python_version_ok"),
        "ollama_running": review.get("ollama_running"),
        "ollama_note": review.get("ollama_note"),
        "missing_configs": missing_configs,
        "missing_directories": missing_dirs,
    }
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    sys.exit(main())
