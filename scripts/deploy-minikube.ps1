param([switch]$SkipBuild)
$ErrorActionPreference='Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
function Check-Exit { if ($LASTEXITCODE -ne 0) { throw "Command failed with exit code $LASTEXITCODE" } }
if (-not $SkipBuild) {
    & mvn -B verify -ntp
    Check-Exit
    & docker compose build
    Check-Exit
}
& minikube start
Check-Exit
foreach ($image in @('mysql:8.0','apache/kafka:3.9.1','tx2/product-service:local','tx2/order-service:local','tx2/api-gateway:local')) {
    Write-Host "Loading $image into Minikube"
    & minikube image load --daemon $image
    Check-Exit
}
& minikube kubectl -- apply -f k8s/
Check-Exit
foreach ($service in @('product-service','order-service','api-gateway')) {
    # A local tag is reused, so restart pods after loading its new image digest.
    & minikube kubectl -- -n tx2-ecommerce rollout restart "deployment/$service"
    Check-Exit
}
foreach ($deployment in @('mysql-db','kafka','product-service','order-service','api-gateway')) {
    & minikube kubectl -- -n tx2-ecommerce rollout status "deployment/$deployment" --timeout=300s
    Check-Exit
}
Write-Host 'Ready. Open a new terminal and run:'
Write-Host 'minikube kubectl -- -n tx2-ecommerce port-forward service/api-gateway 18081:8080'
Write-Host 'API: http://localhost:18081/api/products'
