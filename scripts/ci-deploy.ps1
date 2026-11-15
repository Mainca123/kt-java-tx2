# Run by a Windows GitLab SHELL runner under the account that owns Minikube.
$ErrorActionPreference='Stop'
function Kube {
    & minikube kubectl -- @args
    if ($LASTEXITCODE -ne 0) { throw "kubectl failed: $args" }
}
if (-not $env:CI_REGISTRY_IMAGE -or -not $env:CI_COMMIT_SHA) { throw 'Run from GitLab CI' }
if (-not $env:REGISTRY_PULL_USER -or -not $env:REGISTRY_PULL_PASSWORD) {
    throw 'Set masked GitLab variables REGISTRY_PULL_USER and REGISTRY_PULL_PASSWORD to a deploy token with read_registry permission'
}
Kube apply -f k8s/00-namespace.yaml
# Persistent deploy token is needed because a job token expires after the job.
$secretYaml = & minikube kubectl -- -n tx2-ecommerce create secret docker-registry gitlab-registry --docker-server=$env:CI_REGISTRY --docker-username=$env:REGISTRY_PULL_USER --docker-password=$env:REGISTRY_PULL_PASSWORD --dry-run=client -o yaml
if ($LASTEXITCODE -ne 0) { throw 'Cannot construct registry secret' }
$secretYaml | & minikube kubectl -- apply -f -
if ($LASTEXITCODE -ne 0) { throw 'Cannot apply registry secret' }
# Render in memory; do not put credentials into the checkout.
Get-ChildItem -LiteralPath k8s -Filter '*.yaml' | Sort-Object Name | ForEach-Object {
    $manifest=Get-Content -LiteralPath $_.FullName -Raw
    foreach ($service in @('product-service','order-service','api-gateway')) {
        $manifest=$manifest.Replace("tx2/${service}:local","$($env:CI_REGISTRY_IMAGE)/${service}:$($env:CI_COMMIT_SHA)")
    }
    if ($_.Name.StartsWith('05-')) {
        $manifest=$manifest.Replace('      containers:',"      imagePullSecrets:`n      - name: gitlab-registry`n      containers:")
    }
    $manifest | & minikube kubectl -- apply -f -
    if ($LASTEXITCODE -ne 0) { throw "Apply failed: $($_.Name)" }
}
foreach ($service in @('mysql-db','kafka','product-service','order-service','api-gateway')) {
    Kube -n tx2-ecommerce rollout status "deployment/$service" --timeout=300s
}
