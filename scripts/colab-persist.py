"""Persist and verify an already-ingested month from VM storage to mounted Drive."""

import json
import os
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, "/content/urbanflow/pipelines/src")

from urbanflow_etl.ingestion.download import checksum, write_json  # noqa: E402

source = Path("/content/urbanflow-data/raw")
destination = Path("/content/drive/MyDrive/UrbanFlow/data/raw")
if not destination.parents[2].is_dir():
    raise RuntimeError("Google Drive is not mounted")
destination.mkdir(parents=True, exist_ok=True)
manifest_name = os.environ.get("URBANFLOW_MANIFEST", "2025-01-manifest.json")
manifest = json.loads((source / manifest_name).read_text())

for item in manifest["files"]:
    name = item["name"]
    if Path(name).name != name:
        raise ValueError("Unsafe manifest filename")
    original = source / name
    target = destination / name
    expected = item["sha256"]
    if checksum(original) != expected:
        raise ValueError(f"VM source checksum mismatch: {name}")
    if target.exists():
        if checksum(target) != expected:
            raise ValueError(f"Existing Drive file differs; preserved without overwriting: {name}")
    else:
        partial = target.with_name(name + ".partial")
        shutil.copyfile(original, partial)
        if checksum(partial) != expected:
            raise ValueError(f"Drive copy checksum mismatch: {name}")
        partial.replace(target)
    print(f"Drive verified: {name} ({target.stat().st_size:,} bytes)", flush=True)

write_json(destination / manifest_name, manifest)
status = {
    "state": "complete",
    "period": manifest["period"],
    "files": len(manifest["files"]),
    "total_bytes": sum(item["bytes"] for item in manifest["files"]),
    "persisted_at": datetime.now(UTC).isoformat(),
    "destination": "My Drive/UrbanFlow/data/raw",
    "verification": "SHA-256 of each VM source and each persisted Drive file",
}
write_json(destination / "download-progress.json", status)
print("URBANFLOW_DRIVE_PERSISTED", json.dumps(status), flush=True)
