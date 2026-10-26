import hashlib
import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import pytest
from urbanflow_etl.ingestion.download import download_dataset, validate_file


@pytest.fixture
def source_server(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "trips.parquet").write_bytes(b"PAR1" + b"fixture" * 10 + b"PAR1")
    handler = partial(SimpleHTTPRequestHandler, directory=str(source))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}", source
    server.shutdown()
    server.server_close()
    thread.join()


def test_download_integrity_reuse_and_corruption_recovery(source_server, tmp_path):
    url, source = source_server
    config = {
        "dataset": "fixture",
        "period": "2025-01",
        "files": [
            {
                "name": "trips.parquet",
                "url": f"{url}/trips.parquet",
                "kind": "parquet",
            }
        ],
    }
    output = tmp_path / "output"
    first = download_dataset(config, output)
    target = output / "trips.parquet"
    expected = hashlib.sha256((source / "trips.parquet").read_bytes()).hexdigest()
    assert first["files"][0]["sha256"] == expected
    first_mtime = target.stat().st_mtime_ns
    download_dataset(config, output)
    assert target.stat().st_mtime_ns == first_mtime
    target.write_bytes(b"corrupt")
    repaired = download_dataset(config, output)
    assert repaired["files"][0]["sha256"] == expected
    assert not list(output.glob("*.partial"))


def test_invalid_source_never_becomes_completed_file(source_server, tmp_path):
    url, source = source_server
    (source / "trips.parquet").write_bytes(b"<html>upstream failure</html>")
    config = {
        "dataset": "fixture",
        "period": "2025-01",
        "files": [
            {
                "name": "trips.parquet",
                "url": f"{url}/trips.parquet",
                "kind": "parquet",
            }
        ],
    }
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="signature"):
        download_dataset(config, output)
    assert not (output / "trips.parquet").exists()
    assert json.loads((output / "download-progress.json").read_text())["state"] == "failed"


def test_reject_path_traversal(tmp_path):
    config = {
        "dataset": "fixture",
        "period": "2025-01",
        "files": [
            {
                "name": "../escape",
                "url": "http://127.0.0.1/never",
                "kind": "parquet",
            }
        ],
    }
    with pytest.raises(ValueError, match="Unsafe"):
        download_dataset(config, tmp_path / "output")
    assert not (tmp_path / "escape").exists()


def test_lookup_duplicate_ids_are_rejected(tmp_path):
    lookup = tmp_path / "zones.csv"
    lookup.write_text("LocationID,Borough,Zone\n1,Queens,A\n1,Queens,B\n")
    with pytest.raises(ValueError, match="duplicate"):
        validate_file(lookup, "zone_lookup")
