param(
    [Parameter(Position = 0)]
    [ValidateSet('start', 'stop', 'status', 'logs', 'check')]
    [string]$Action = 'start',
    [switch]$NoBrowser
)

# Windows PowerShell 5.1 compatible. No machine-wide policy or PATH changes.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$logDir = Join-Path $projectRoot 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logPath = Join-Path $logDir ('launcher-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.log')
$statePath = Join-Path $logDir 'launcher-state.json'
$originalPort = $env:GATEWAY_PORT
$exitCode = 0

function Write-Step([string]$Message) {
    Write-Host $Message
    Add-Content -LiteralPath $logPath -Value $Message -Encoding UTF8
}

function Invoke-Docker([string[]]$DockerArguments, [switch]$Quiet) {
    $savedPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $output = New-Object 'System.Collections.Generic.List[string]'
        & $script:dockerExe @DockerArguments 2>&1 | ForEach-Object {
            $line = [string]$_
            $output.Add($line)
            Add-Content -LiteralPath $logPath -Value $line -Encoding UTF8
            if (-not $Quiet) { Write-Host $line }
        }
        $code = $LASTEXITCODE
        if ($code -ne 0) { throw "Docker command failed (exit $code). See: $logPath" }
        return $output
    }
    finally { $ErrorActionPreference = $savedPreference }
}

function Get-DockerOs {
    $savedPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $result = & $script:dockerExe info --format '{{.OSType}}' 2>$null
        if ($LASTEXITCODE -eq 0) { return ([string]$result).Trim() }
        return ''
    }
    finally { $ErrorActionPreference = $savedPreference }
}

function Test-PortAvailable([int]$Port) {
    $listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, $Port)
    try { $listener.Start(); return $true }
    catch { return $false }
    finally { $listener.Stop() }
}

function Get-GatewayMapping {
    try {
        $output = @(Invoke-Docker -DockerArguments ($script:composeArgs + @('port', 'api-gateway', '8080')) -Quiet)
        foreach ($line in $output) {
            if ([string]$line -match ':(\d+)\s*$') { return [int]$Matches[1] }
        }
    }
    catch { } # No gateway container exists on a first run.
    return 0
}

Push-Location $projectRoot
try {
    Write-Step '=== E-COMMERCE MICROSERVICES ==='
    Write-Step "Action: $Action"
    $dockerCommand = Get-Command docker.exe -ErrorAction SilentlyContinue
    if ($dockerCommand) { $script:dockerExe = $dockerCommand.Source }
    else {
        $dockerCandidates = @(
            (Join-Path $env:ProgramFiles 'Docker\Docker\resources\bin\docker.exe'),
            (Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin\docker.exe')
        )
        $script:dockerExe = $dockerCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
        if (-not $script:dockerExe) {
            throw 'Docker Desktop is missing. Read HUONG_DAN_CHAY.md, install Docker Desktop, then run this file again. Download: https://docs.docker.com/desktop/setup/install/windows-install/'
        }
    }
    $script:composeArgs = @('compose', '-f', (Join-Path $projectRoot 'compose.run.yml'))
    Invoke-Docker -DockerArguments @('compose', 'version') | Out-Null
    $dockerOs = Get-DockerOs
    if (-not $dockerOs -and $Action -eq 'start') {
        $desktopCandidates = @(
            (Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'),
            (Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\Docker Desktop.exe')
        )
        $desktopExe = $desktopCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
        if ($desktopExe) {
            Write-Step 'Starting Docker Desktop. Please finish any first-time setup in Docker Desktop.'
            Start-Process -FilePath $desktopExe -WindowStyle Hidden
            $deadline = (Get-Date).AddSeconds(180)
            while (-not $dockerOs -and (Get-Date) -lt $deadline) {
                Start-Sleep -Seconds 5
                $dockerOs = Get-DockerOs
            }
        }
    }
    if (-not $dockerOs) { throw 'Docker Engine is not ready. Open Docker Desktop, wait for Engine running, then try again.' }
    if ($dockerOs -ne 'linux') { throw 'Please switch Docker Desktop to Linux containers, then try again.' }
    Invoke-Docker -DockerArguments ($script:composeArgs + @('config', '--quiet')) -Quiet | Out-Null
    if ($Action -eq 'check') {
        Write-Step 'OK: Docker Engine (Linux), Docker Compose and project configuration are ready.'
        Write-Step 'No host Java, Maven, MySQL, Kafka or Minikube installation is required.'
    }
    elseif ($Action -eq 'stop') {
        Invoke-Docker -DockerArguments ($script:composeArgs + @('stop', '--timeout', '30')) | Out-Null
        Write-Step 'Stopped this project. Database and Kafka volumes were preserved.'
    }
    elseif ($Action -eq 'logs') {
        Invoke-Docker -DockerArguments ($script:composeArgs + @('logs', '--no-color', '--tail', '100')) | Out-Null
    }
    elseif ($Action -eq 'status') {
        Invoke-Docker -DockerArguments ($script:composeArgs + @('ps', '--all')) | Out-Null
        $mappedPort = Get-GatewayMapping
        if ($mappedPort) { Write-Step "Gateway: http://localhost:$mappedPort" }
    }
    else {
        $requestedPort = 18080
        $configuredPort = $env:GATEWAY_PORT
        if (-not $configuredPort -and (Test-Path -LiteralPath '.env')) {
            foreach ($line in Get-Content -LiteralPath '.env') {
                if ($line -match '^\s*GATEWAY_PORT\s*=\s*["'']?(\d+)["'']?\s*(?:#.*)?$') { $configuredPort = $Matches[1] }
            }
        }
        if ($configuredPort) {
            $parsedPort = 0
            if (-not [int]::TryParse($configuredPort, [ref]$parsedPort) -or $parsedPort -lt 1024 -or $parsedPort -gt 65535) {
                throw 'GATEWAY_PORT must be an integer between 1024 and 65535. Check your environment or .env file.'
            }
            $requestedPort = $parsedPort
        }
        $mappedPort = Get-GatewayMapping
        if ($mappedPort -and -not $configuredPort) { $requestedPort = $mappedPort }
        $chosenPort = $requestedPort
        if ($chosenPort -ne $mappedPort -and -not (Test-PortAvailable $chosenPort)) {
            $chosenPort = 0
            foreach ($candidate in 18080..18100) {
                if ($candidate -eq $mappedPort -or (Test-PortAvailable $candidate)) { $chosenPort = $candidate; break }
            }
            if (-not $chosenPort) { throw 'No available local port in 18080-18100. Set a free GATEWAY_PORT in .env and retry.' }
            Write-Step "Port $requestedPort is busy/reserved. Using port $chosenPort instead."
        }
        $env:GATEWAY_PORT = [string]$chosenPort
        $url = "http://localhost:$chosenPort"
        Write-Step 'Building Java applications inside Docker. The first run needs Internet and can take several minutes.'
        # All three images share the same cached Maven build stage.
        Invoke-Docker -DockerArguments (@('compose', '--parallel', '1', '--progress', 'plain', '-f', (Join-Path $projectRoot 'compose.run.yml'), 'build')) | Out-Null
        Write-Step 'Starting MySQL, Kafka, Product Service, Order Service and API Gateway...'
        Invoke-Docker -DockerArguments ($script:composeArgs + @('up', '-d', '--wait', '--wait-timeout', '420')) | Out-Null
        Write-Step 'Checking the gateway and read-only APIs...'
        foreach ($path in @('/actuator/health', '/api/products', '/api/orders')) {
            $response = Invoke-WebRequest -UseBasicParsing -Uri ($url + $path) -TimeoutSec 30
            if ($response.StatusCode -ne 200) { throw "HTTP check failed: $path" }
            if ($path -eq '/actuator/health') {
                # PS 5.1 returns Byte[] for Spring's vendor-specific JSON content type.
                $healthJson = $response.Content
                if ($healthJson -is [byte[]]) { $healthJson = [System.Text.Encoding]::UTF8.GetString($healthJson) }
                if (($healthJson | ConvertFrom-Json).status -ne 'UP') { throw 'Gateway health is not UP.' }
            }
        }
        @{ url = $url; port = $chosenPort; startedAt = (Get-Date -Format 'o') } | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8
        Write-Step ''
        Write-Step "READY: $url"
        Write-Step 'To stop: run.bat stop (your data will be kept).'
        if (-not $NoBrowser) { Start-Process $url }
    }
}
catch {
    $exitCode = 1
    Write-Step ("ERROR: " + $_.Exception.Message)
    if ($script:dockerExe -and $Action -eq 'start' -and $script:composeArgs) {
        try { Invoke-Docker -DockerArguments ($script:composeArgs + @('ps', '--all')) | Out-Null } catch { }
        try { Invoke-Docker -DockerArguments ($script:composeArgs + @('logs', '--no-color', '--tail', '35')) | Out-Null } catch { }
    }
    Write-Step 'Read HUONG_DAN_CHAY.md for troubleshooting. Fix the issue, then run run.bat again.'
}
finally {
    $env:GATEWAY_PORT = $originalPort
    Pop-Location
    Write-Host "Log: $logPath"
}
exit $exitCode
