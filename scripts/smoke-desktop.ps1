param([string]$Executable = 'release/win-unpacked/UrbanFlow.exe', [string]$Report = '.cache/desktop-smoke.json')
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$executablePath = [IO.Path]::GetFullPath((Join-Path $root $Executable))
$reportPath = [IO.Path]::GetFullPath((Join-Path $root $Report))
if (-not (Test-Path -LiteralPath $executablePath)) { throw "Missing desktop executable: $executablePath" }
if (Test-Path -LiteralPath $reportPath) { Remove-Item -LiteralPath $reportPath }
$before = @(Get-Process -Name urbanflow-api -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
$process = Start-Process -FilePath $executablePath -ArgumentList ('--smoke-output="' + $reportPath + '"') -WindowStyle Hidden -PassThru
try {
    for ($attempt = 0; $attempt -lt 120; $attempt++) {
        if ($process.WaitForExit(1000)) { break }
    }
    if (-not $process.HasExited) { throw 'Desktop smoke test exceeded 120 seconds.' }
    if ($process.ExitCode -ne 0) { throw "Desktop exited with status $($process.ExitCode)." }
    if (-not (Test-Path -LiteralPath $reportPath)) { throw 'Desktop did not write its smoke report; inspect backend.log.' }
    $result = Get-Content -Raw -LiteralPath $reportPath | ConvertFrom-Json
    if ($result.apiStatus -ne 200 -or -not $result.dashboardReady -or -not $result.nodeDisabled -or -not $result.desktop -or $result.rootChildren -lt 1) { throw 'Desktop smoke report contains failed checks.' }
    Start-Sleep -Milliseconds 500
    $leaked = @(Get-Process -Name urbanflow-api -ErrorAction SilentlyContinue | Where-Object { $_.Id -notin $before })
    if ($leaked.Count -gt 0) { throw 'A new backend process remained after desktop shutdown.' }
    Write-Output "PASS desktop startup, renderer, API, security flags, screenshot, and backend shutdown: $reportPath"
} finally {
    if (-not $process.HasExited) { Stop-Process -Id $process.Id }
}
