param([switch]$SkipBuild)
$ErrorActionPreference='Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not $SkipBuild) {
    & mvn -B verify -ntp
    if ($LASTEXITCODE -ne 0) { throw 'Maven build failed' }
}
& docker compose up -d --build --wait --wait-timeout 300
if ($LASTEXITCODE -ne 0) { throw 'Docker startup failed; run docker compose logs --tail 100' }
Write-Host 'Gateway: http://localhost:18080'
Write-Host 'Run tests: postman collection run postman/tx2.postman_collection.json --no-report-events'
