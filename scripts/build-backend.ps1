param([string]$Python = "$PSScriptRoot/../.venv/Scripts/python.exe")
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Push-Location $root
try {
    & $Python scripts/build-icon.py
    if ($LASTEXITCODE -ne 0) { throw 'Windows icon generation failed.' }
    & $Python -m PyInstaller --noconfirm --clean --onedir --console --name urbanflow-api --distpath artifacts/backend --workpath .cache/pyinstaller --specpath .cache/pyinstaller --paths apps/api --collect-submodules app --collect-submodules uvicorn apps/api/app/desktop_entry.py
    if ($LASTEXITCODE -ne 0) { throw 'Backend packaging failed.' }
    if (-not (Test-Path -LiteralPath 'artifacts/backend/urbanflow-api/urbanflow-api.exe')) { throw 'Backend executable was not produced.' }
} finally { Pop-Location }
