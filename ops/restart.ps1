param(
  [switch]$Build,
  [ValidateSet("auto", "docker", "local")]
  [string]$Mode = "auto",
  [string]$SeeSeaUrl = $(if ($env:SEESEA_BASE_URL) { $env:SEESEA_BASE_URL } else { "http://127.0.0.1:18080" })
)

$ErrorActionPreference = "Stop"
$rootDir = Split-Path -Path $PSScriptRoot -Parent
$composeFile = Join-Path $PSScriptRoot "docker-compose.yml"

function Get-ComposeCommand {
  if (Get-Command docker -ErrorAction SilentlyContinue) {
    try {
      docker compose version *> $null
      if ($LASTEXITCODE -eq 0) {
        return "docker compose"
      }
    } catch {
      # fallback to docker-compose
    }
  }

  if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
    return "docker-compose"
  }

  return $null
}

function Stop-ListeningPortProcess {
  param([int]$Port)
  $listeners = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
  if (-not $listeners) {
    return
  }

  $processIds = $listeners | Select-Object -ExpandProperty OwningProcess -Unique
  foreach ($processId in $processIds) {
    try {
      Stop-Process -Id $processId -Force -ErrorAction Stop
      Write-Host "Stopped process $processId on port $Port"
    } catch {
      Write-Warning "Failed to stop process ${processId} on port ${Port}: $($_.Exception.Message)"
    }
  }
}

function Wait-HttpReady {
  param(
    [string]$Name,
    [string]$Url,
    [int]$TimeoutSeconds = 30,
    [int]$IntervalSeconds = 1
  )

  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  $lastError = $null

  while ((Get-Date) -lt $deadline) {
    try {
      $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 5 -UseBasicParsing
      Write-Host ("{0}: OK ({1})" -f $Name, $response.StatusCode)
      return $true
    } catch {
      $lastError = $_.Exception.Message
      Start-Sleep -Seconds $IntervalSeconds
    }
  }

  Write-Warning ("{0}: Not ready after {1}s ({2})" -f $Name, $TimeoutSeconds, $lastError)
  return $false
}

function Start-LocalMode {
  $backendDir = Join-Path $rootDir "backend"
  $frontendDir = Join-Path $rootDir "frontend"
  $venvScripts = Join-Path $backendDir ".venv\Scripts"
  $uvicornExe = Join-Path $venvScripts "uvicorn.exe"
  $astroCmd = Join-Path $frontendDir "node_modules\.bin\astro.CMD"

  foreach ($requiredPath in @($backendDir, $frontendDir, $uvicornExe, $astroCmd)) {
    if (-not (Test-Path $requiredPath)) {
      throw "Required path not found for local mode: $requiredPath"
    }
  }

  Write-Host "Checking external SeeSea at $SeeSeaUrl ..."
  Wait-HttpReady -Name "SeeSea" -Url "$SeeSeaUrl/api/health" -TimeoutSeconds 10 | Out-Null

  Write-Host "Stopping existing local API/frontend services..."
  Stop-ListeningPortProcess -Port 8000
  Stop-ListeningPortProcess -Port 4321

  Start-Sleep -Seconds 1

  $env:SEESEA_BASE_URL = $SeeSeaUrl

  Write-Host "Starting API on http://127.0.0.1:8000 ..."
  Start-Process -FilePath $uvicornExe `
    -ArgumentList @("app.main:app", "--host", "127.0.0.1", "--port", "8000") `
    -WorkingDirectory $backendDir `
    -WindowStyle Hidden

  Start-Sleep -Seconds 2

  Write-Host "Starting frontend on http://127.0.0.1:4321 ..."
  $frontendStart = "$env:PUBLIC_API_BASE='http://127.0.0.1:8000/api'; & '$astroCmd' dev --host 127.0.0.1 --port 4321"
  Start-Process -FilePath "powershell.exe" `
    -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $frontendStart) `
    -WorkingDirectory $frontendDir `
    -WindowStyle Hidden

  Start-Sleep -Seconds 2

  Write-Host "Local services launch attempted. Waiting for health checks:"
  foreach ($item in @(
      @{ Name = "API"; Url = "http://127.0.0.1:8000/healthz" },
      @{ Name = "Frontend"; Url = "http://127.0.0.1:4321/" }
    )) {
    Wait-HttpReady -Name $item.Name -Url $item.Url | Out-Null
  }
}

$compose = $null
if ($Mode -ne "local") {
  $compose = Get-ComposeCommand
}

if ($Mode -eq "docker" -and -not $compose) {
  throw "Mode is 'docker' but neither 'docker compose' nor 'docker-compose' was found."
}

if ($compose) {
  if (-not (Test-Path $composeFile)) {
    throw "Cannot find compose file: $composeFile"
  }

  Write-Host "Checking external SeeSea at $SeeSeaUrl ..."
  Wait-HttpReady -Name "SeeSea" -Url "$SeeSeaUrl/api/health" -TimeoutSeconds 10 | Out-Null

  $downCmd = "$compose -f `"$composeFile`" down --remove-orphans"
  $upFlags = "up -d --remove-orphans"
  if ($Build) {
    $upFlags = "$upFlags --build"
  }
  $upCmd = "$compose -f `"$composeFile`" $upFlags"

  Write-Host "Stopping docker services..."
  Invoke-Expression $downCmd

  Write-Host "Starting docker services..."
  Invoke-Expression $upCmd

  Write-Host "Docker service status:"
  Invoke-Expression "$compose -f `"$composeFile`" ps"
} else {
  Write-Host "Docker command not found, switching to local mode."
  Start-LocalMode
}
