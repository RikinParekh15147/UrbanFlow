// Run after creating artifacts/urbanflow-pipeline.zip with pipelines/ and configs/.
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
const digest = createHash('sha256').update(await readFile('artifacts/urbanflow-pipeline.zip')).digest('hex');
const md = text => ({ cell_type: 'markdown', metadata: {}, source: text });
const code = text => ({ cell_type: 'code', metadata: {}, source: text.trimEnd(), execution_count: null, outputs: [] });
const notebook = {
  nbformat: 4, nbformat_minor: 5,
  metadata: { colab: { name: 'UrbanFlow — January 2025 ingestion' }, kernelspec: { display_name: 'Python 3', name: 'python3' }, language_info: { name: 'python' } },
  cells: [
    md('# UrbanFlow · January 2025 ingestion\n\nRun all cells in a standard **CPU** Colab runtime. Approve Google Drive access when prompted. Keep `urbanflow-pipeline.zip` at the root of My Drive next to this notebook. No MongoDB credentials or paid runtime are needed.\n\nThe notebook orchestrates the reusable Python package; ingestion logic stays in `pipelines/`. Raw data, checksums and progress persist in `My Drive/UrbanFlow/data/raw`. Re-running verifies existing downloads.'),
    code('from google.colab import drive\n\ndrive.mount("/content/drive")\n'),
    code(`import hashlib\nimport sys\nimport zipfile\nfrom pathlib import Path\n\nbundle = Path("/content/drive/MyDrive/urbanflow-pipeline.zip")\nexpected_sha256 = "${digest}"\nif not bundle.is_file():\n    raise FileNotFoundError("Put urbanflow-pipeline.zip at the root of My Drive, then rerun.")\nif hashlib.sha256(bundle.read_bytes()).hexdigest() != expected_sha256:\n    raise ValueError(\n        "Pipeline bundle checksum mismatch. Use the bundle supplied with this notebook."\n    )\nworkspace = Path("/content/urbanflow").resolve()\nworkspace.mkdir(parents=True, exist_ok=True)\nwith zipfile.ZipFile(bundle) as archive:\n    for member in archive.infolist():\n        if not (workspace / member.filename).resolve().is_relative_to(workspace):\n            raise ValueError("Unsafe archive path")\n    archive.extractall(workspace)\nsys.path.insert(0, str(workspace / "pipelines" / "src"))\nprint("Verified reusable pipeline:", expected_sha256)\n`),
    code('import json\n\nfrom urbanflow_etl.ingestion.download import download_dataset\n\nconfig = json.loads((workspace / "configs" / "yellow-2025-01.json").read_text())\noutput = Path("/content/drive/MyDrive/UrbanFlow/data/raw")\nmanifest = download_dataset(config, output)\nprint(json.dumps(manifest, indent=2))\n'),
    code('progress = json.loads((output / "download-progress.json").read_text())\nprint(json.dumps(progress, indent=2))\nprint("Persistent data:", output)\n'),
    md('## Local fallback\n\nIf the download stalls, run `node scripts/download-data.mjs` from the repository on Windows. Upload the files and `2025-01-manifest.json` from `data/raw/` to `My Drive/UrbanFlow/data/raw/`, then rerun this notebook. Existing files are checksum-verified before reuse.\n\nThis notebook prepares source data. Spark transformations and MongoDB publication are subsequent milestones; no analytical results have been fabricated.')
  ]
};
await writeFile('notebooks/00_ingestion_colab.ipynb', JSON.stringify(notebook, null, 2) + '\n');
console.log(`Notebook generated with bundle SHA-256 ${digest}`);
