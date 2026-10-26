"""Create a small, portable source bundle with no credentials, caches or data."""

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, default=Path("artifacts/urbanflow-pipeline.zip"))
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
destination = root / args.output
destination.parent.mkdir(exist_ok=True)
sources = [root / "pipelines" / "pyproject.toml"]
sources.extend(sorted((root / "pipelines" / "src").rglob("*.py")))
sources.extend(sorted((root / "configs").glob("*.json")))
sources.extend(sorted((root / "pipelines" / "tests").glob("test_spark*.py")))
with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
    for source in sources:
        archive.write(source, source.relative_to(root).as_posix())
print(f"Packaged {len(sources)} source files: {destination}")
