param([int]$Port=18081)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$logs=Join-Path $root 'logs'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
if (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue) {
    Write-Host "Port $Port is already listening. URL: http://localhost:$Port"
    exit 0
}
$minikube=(Get-Command minikube -ErrorAction Stop).Source
$process=Start-Process -FilePath $minikube -ArgumentList @('kubectl','--','-n','tx2-ecommerce','port-forward','service/api-gateway',"${Port}:8080") -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logs 'port-forward.txt') -RedirectStandardError (Join-Path $logs 'port-forward-errors.txt')
Set-Content -LiteralPath (Join-Path $logs 'port-forward.pid') -Value $process.Id
Write-Host "Port-forward started (PID $($process.Id)): http://localhost:$Port"
