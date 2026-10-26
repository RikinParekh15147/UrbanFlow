"""Create a small, portable source bundle with no credentials, caches or data."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parent.parent
destination = root / "artifacts" / "urbanflow-pipeline.zip"
destination.parent.mkdir(exist_ok=True)
sources = [root / "pipelines" / "pyproject.toml"]
sources.extend(sorted((root / "pipelines" / "src").rglob("*.py")))
sources.extend(sorted((root / "configs").glob("*.json")))
with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
    for source in sources:
        archive.write(source, source.relative_to(root).as_posix())
print(f"Packaged {len(sources)} source files: {destination}")
