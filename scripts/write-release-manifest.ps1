$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Push-Location $root
try {
    $version = (Get-Content -Raw -LiteralPath 'apps/desktop/package.json' | ConvertFrom-Json).version
    $files = @(
        Get-Item -LiteralPath "release/UrbanFlow-Setup-$version.exe"
        Get-Item -LiteralPath "release/UrbanFlow-Portable-$version.zip"
    )
    $artifacts = foreach ($file in $files) {
        $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        "$hash  $($file.Name)" | Set-Content -LiteralPath "$($file.FullName).sha256" -Encoding ascii
        [ordered]@{ file = $file.Name; bytes = $file.Length; sha256 = $hash }
    }
    [ordered]@{
        version = $version
        built_at = [DateTime]::UtcNow.ToString('o')
        snapshot = (Get-Content -Raw -LiteralPath 'data/serving/manifest.json' | ConvertFrom-Json)
        artifacts = @($artifacts)
    } | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath 'release/release-manifest.json' -Encoding utf8
} finally { Pop-Location }
