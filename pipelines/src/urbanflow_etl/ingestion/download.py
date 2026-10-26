"""Dependency-free ingestion, shared by local runs and Colab.

Checksum manifests establish local integrity, not publisher authenticity.
Partial downloads are never exposed as completed source files.
"""

import argparse
import csv
import hashlib
import json
import time
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, document: dict) -> None:
    temporary = path.with_name(path.name + ".partial")
    temporary.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def validate_file(path: Path, kind: str) -> None:
    if kind == "parquet":
        if path.stat().st_size < 12:
            raise ValueError("Truncated Parquet file")
        with path.open("rb") as stream:
            first = stream.read(4)
            stream.seek(-4, 2)
            last = stream.read(4)
        if first != b"PAR1" or last != b"PAR1":
            raise ValueError("Invalid Parquet signature")
    elif kind == "zone_lookup":
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if not {"LocationID", "Borough", "Zone"}.issubset(reader.fieldnames or []):
                raise ValueError("Zone lookup is missing required columns")
            rows = list(reader)
            if not rows or len({row["LocationID"] for row in rows}) != len(rows):
                raise ValueError("Zone lookup is empty or has duplicate IDs")
    elif kind == "zip":
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise ValueError("Corrupt zone geometry archive")
            if not any(name.endswith(".shp") for name in archive.namelist()):
                raise ValueError("Zone geometry archive has no shapefile")


def download_dataset(config: dict, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / f"{config['period']}-manifest.json"
    progress_path = output / "download-progress.json"
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"files": []}
    manifest = {
        "dataset": config["dataset"],
        "period": config["period"],
        "downloaded_at": datetime.now(UTC).isoformat(),
        "files": [],
    }
    try:
        for source in config["files"]:
            name = source["name"]
            if Path(name).name != name or "/" in name or "\\" in name or name in {".", ".."}:
                raise ValueError("Unsafe destination filename")
            target = output / name
            prior = next(
                (
                    row
                    for row in previous["files"]
                    if row["name"] == name and row["url"] == source["url"]
                ),
                None,
            )
            if (
                prior
                and target.exists()
                and target.stat().st_size == prior["bytes"]
                and checksum(target) == prior["sha256"]
            ):
                validate_file(target, source["kind"])
                manifest["files"].append(prior)
                print(f"{name}: verified existing source", flush=True)
                continue
            started = time.monotonic()
            last_report = 0.0
            partial = target.with_name(name + ".partial")
            request = Request(source["url"], headers={"User-Agent": "UrbanFlow/0.1"})
            digest = hashlib.sha256()
            received = 0
            with urlopen(request, timeout=60) as response, partial.open("wb") as stream:
                expected = int(response.headers.get("Content-Length", 0)) or None
                while chunk := response.read(1024 * 1024):
                    stream.write(chunk)
                    digest.update(chunk)
                    received += len(chunk)
                    now = time.monotonic()
                    if now - last_report >= 2:
                        elapsed = now - started
                        progress = {
                            "state": "downloading",
                            "file": name,
                            "bytes": received,
                            "total_bytes": expected,
                            "elapsed_seconds": round(elapsed, 2),
                            "mb_per_second": round(received / max(elapsed, 0.001) / 1e6, 2),
                            "updated_at": datetime.now(UTC).isoformat(),
                        }
                        write_json(progress_path, progress)
                        print(json.dumps(progress), flush=True)
                        last_report = now
            if expected is not None and received != expected:
                raise ValueError(f"Incomplete download: {received}/{expected}")
            validate_file(partial, source["kind"])
            partial.replace(target)
            manifest["files"].append(
                {
                    **source,
                    "bytes": received,
                    "sha256": digest.hexdigest(),
                    "elapsed_seconds": round(time.monotonic() - started, 3),
                }
            )
            write_json(manifest_path, manifest)
            print(f"{name}: complete ({received:,} bytes)", flush=True)
        write_json(manifest_path, manifest)
        write_json(progress_path, {"state": "complete", "files": len(manifest["files"])})
        return manifest
    except Exception as error:
        write_json(progress_path, {"state": "failed", "error": str(error)})
        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download official TLC data with progress and checksums"
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    download_dataset(config, args.output)


if __name__ == "__main__":
    main()
