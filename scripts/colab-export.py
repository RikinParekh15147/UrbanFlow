"""Archive reproducibility outputs and verify persistent Drive copies."""

import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile

sys.path.insert(0, "/content/urbanflow-analytics/pipelines/src")
from urbanflow_etl.ingestion.download import checksum, write_json  # noqa: E402

root = Path("/content/urbanflow-results")
manifest = json.loads((root / "serving/manifest.json").read_text())
destination = Path("/content/drive/MyDrive/UrbanFlow/runs") / manifest["run_id"]
if not Path("/content/drive/MyDrive").is_dir():
    raise RuntimeError("Drive is not mounted")
destination.mkdir(parents=True, exist_ok=True)
archive = Path("/content/urbanflow-parquet.zip")
with ZipFile(archive, "w", compression=ZIP_STORED) as output:
    for folder in ("curated", "parquet"):
        for source in sorted((root / folder).rglob("*")):
            if source.is_file():
                output.write(source, source.relative_to(root).as_posix())
files = [
    (Path("/content/urbanflow-serving.zip"), "serving.zip"),
    (archive, "curated-and-aggregate-parquet.zip"),
    (Path("/content/urbanflow-analytics.zip"), "executed-source.zip"),
    (root / "serving/manifest.json", "manifest.json"),
    (root / "serving/benchmarks.jsonl", "benchmarks.jsonl"),
]
report = {
    "status": "complete",
    "run_id": manifest["run_id"],
    "persisted_at": datetime.now(UTC).isoformat(),
    "files": [],
    "destination": f"My Drive/UrbanFlow/runs/{manifest['run_id']}",
}
for source, name in files:
    expected = checksum(source)
    target = destination / name
    if target.exists() and checksum(target) != expected:
        raise ValueError(f"Existing archive differs and has been preserved: {name}")
    if not target.exists():
        temporary = target.with_name(name + ".partial")
        shutil.copyfile(source, temporary)
        if checksum(temporary) != expected:
            raise ValueError(f"Drive checksum mismatch: {name}")
        temporary.replace(target)
    report["files"].append({"name": name, "bytes": target.stat().st_size, "sha256": expected})
    print(f"Drive archive verified: {name} ({target.stat().st_size:,} bytes)", flush=True)
write_json(destination / "drive-export-manifest.json", report)
Path("/content/urbanflow-drive-export.json").write_text(json.dumps(report, indent=2) + "\n")
print("DRIVE_EXPORT_VERIFIED", json.dumps(report), flush=True)
