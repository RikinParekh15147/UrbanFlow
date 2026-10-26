"""Run from repository root: uv run python scripts/export-openapi.py."""

import json
from pathlib import Path

from app.main import app

Path("contracts/openapi.json").write_text(json.dumps(app.openapi(), indent=2) + "\n")
