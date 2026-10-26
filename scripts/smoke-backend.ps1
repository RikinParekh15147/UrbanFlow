param([int]$Port = 18765)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$executable = Join-Path $root 'artifacts/backend/urbanflow-api/urbanflow-api.exe'
$arguments = @('--port', $Port, '--snapshot-dir', ('"' + (Join-Path $root 'data/serving') + '"'), '--web-dir', ('"' + (Join-Path $root 'apps/web/dist') + '"'))
$process = Start-Process -FilePath $executable -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardError (Join-Path $root '.cache/backend-smoke.stderr.log') -RedirectStandardOutput (Join-Path $root '.cache/backend-smoke.stdout.log')
try {
    $ready = $false
    for ($attempt = 0; $attempt -lt 150; $attempt++) {
        if ($process.HasExited) { throw 'Packaged backend exited before readiness; inspect .cache/backend-smoke.stderr.log.' }
        try {
            $health = Invoke-RestMethod "http://127.0.0.1:$Port/health" -TimeoutSec 1
            if ($health.service -eq 'urbanflow-api') { $ready = $true; break }
        } catch { Start-Sleep -Milliseconds 200 }
    }
    if (-not $ready) { throw 'Packaged backend did not become ready.' }
    foreach ($path in @('/', '/api/v1/datasets/status', '/api/v1/overview', '/api/v1/demand/hourly', '/api/v1/demand/daily', '/api/v1/zones', '/api/v1/geography/heatmap', '/api/v1/routes/top', '/api/v1/trips/efficiency', '/api/v1/fares/summary', '/api/v1/benchmarks')) {
        $response = Invoke-WebRequest "http://127.0.0.1:$Port$path" -UseBasicParsing -TimeoutSec 60
        if ($response.StatusCode -ne 200) { throw "Unexpected response at $path" }
        Write-Output "PASS $path ($($response.RawContentLength) bytes)"
    }
} finally {
    if (-not $process.HasExited) { Stop-Process -Id $process.Id; $process.WaitForExit() }
}
Write-Output 'PASS packaged backend startup, API requests, frontend assets, and process shutdown.'
