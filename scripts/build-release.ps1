param([switch]$SkipFrontend, [switch]$SkipBackend, [ValidateRange(0, 9)][int]$CompressionLevel = 5)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Push-Location $root
$previousCompression = $env:ELECTRON_BUILDER_COMPRESSION_LEVEL
try {
    if (-not $SkipFrontend) {
        & npm.cmd run build
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
    }
    if (-not $SkipBackend) { & "$PSScriptRoot/build-backend.ps1" }
    & node -e "require('electron')"
    if ($LASTEXITCODE -ne 0) { throw 'Electron runtime installation failed.' }
    if (-not (Test-Path -LiteralPath 'data/serving/manifest.json')) { throw 'Real published snapshot is required in data/serving.' }
    $env:ELECTRON_BUILDER_COMPRESSION_LEVEL = [string]$CompressionLevel
    & npm.cmd run desktop:build
    if ($LASTEXITCODE -ne 0) { throw 'Electron packaging failed.' }
    & "$PSScriptRoot/write-release-manifest.ps1"
} finally {
    $env:ELECTRON_BUILDER_COMPRESSION_LEVEL = $previousCompression
    Pop-Location
}
