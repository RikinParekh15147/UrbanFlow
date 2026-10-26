"""Colab CLI entrypoint: unpack reusable source and ingest into temporary VM storage."""

import hashlib
import json
import os
import sys
from pathlib import Path
from zipfile import ZipFile

bundle = Path("/content/urbanflow-pipeline.zip")
expected = os.environ["URBANFLOW_BUNDLE_SHA256"]
if hashlib.sha256(bundle.read_bytes()).hexdigest() != expected:
    raise ValueError("Pipeline bundle checksum mismatch")
workspace = Path("/content/urbanflow").resolve()
workspace.mkdir(exist_ok=True)
with ZipFile(bundle) as archive:
    for item in archive.infolist():
        if not (workspace / item.filename).resolve().is_relative_to(workspace):
            raise ValueError("Unsafe archive path")
    archive.extractall(workspace)
sys.path.insert(0, str(workspace / "pipelines" / "src"))

from urbanflow_etl.ingestion.download import download_dataset  # noqa: E402

config = json.loads((workspace / "configs" / "yellow-2025-01.json").read_text())
manifest = download_dataset(config, Path("/content/urbanflow-data/raw"))
print("URBANFLOW_INGESTION_COMPLETE", json.dumps(manifest), flush=True)
