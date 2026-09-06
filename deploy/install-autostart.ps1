<#
.SYNOPSIS
    Windows only. Makes YouTube Transcripter start automatically when you log in.

.DESCRIPTION
    Docker already restarts the container by itself (`restart: unless-stopped`
    in docker-compose.yml). For that to happen at boot, Docker Desktop has to
    be running - enable "Start Docker Desktop when you log in" in
    Docker Desktop > Settings > General.

    This script adds a Scheduled Task as a safety net: it re-runs
    `docker compose up -d` at logon, which also recovers the stack after a
    manual `docker compose down`. No administrator rights are required.

    CPU or GPU is read from COMPOSE_FILE in .env - switch with .\mode.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\deploy\install-autostart.ps1
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$TaskName   = 'YouTubeTranscripter'
$EnvFile    = Join-Path $ProjectDir '.env'

$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker) {
    throw 'docker was not found on PATH. Install Docker Desktop and make sure it is running: https://www.docker.com/products/docker-desktop/'
}

if (-not (Test-Path $EnvFile)) {
    Write-Host '==> .env not found, creating it from .env.example'
    Copy-Item (Join-Path $ProjectDir '.env.example') $EnvFile
}

$mode = if (Select-String -Path $EnvFile -Pattern '^COMPOSE_FILE=.*gpu' -Quiet) { 'gpu' } else { 'cpu' }
Write-Host "==> Mode from .env: $mode"

Write-Host '==> Starting the stack now'
Push-Location $ProjectDir
try {
    docker compose up -d
    if ($LASTEXITCODE -ne 0) { throw 'docker compose up failed. Is Docker Desktop running?' }
} finally {
    Pop-Location
}

Write-Host "==> Registering the '$TaskName' scheduled task (at logon)"
$action = New-ScheduledTaskAction -Execute $docker.Source `
                                  -Argument 'compose up -d --remove-orphans' `
                                  -WorkingDirectory $ProjectDir

$trigger = New-ScheduledTaskTrigger -AtLogOn
# Give Docker Desktop a minute to finish booting before we talk to it.
$trigger.Delay = 'PT1M'

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
                                         -DontStopOnIdleEnd `
                                         -ExecutionTimeLimit (New-TimeSpan -Minutes 15) `
                                         -RestartCount 3 `
                                         -RestartInterval (New-TimeSpan -Minutes 2)

Register-ScheduledTask -TaskName $TaskName `
                       -Action $action `
                       -Trigger $trigger `
                       -Settings $settings `
                       -Description 'Starts the YouTube Transcripter container at logon.' `
                       -Force | Out-Null

Write-Host ''
Write-Host 'Done. The app is available at http://localhost:8501'
Write-Host ''
Write-Host 'IMPORTANT - one manual step left:'
Write-Host '  Open Docker Desktop > Settings > General and tick'
Write-Host '  "Start Docker Desktop when you log in".'
Write-Host '  Without it, Docker is not running at logon and nothing can start.'
Write-Host ''
Write-Host "Check the task with:  Get-ScheduledTask -TaskName $TaskName"
Write-Host 'Check the logs with:  docker compose logs -f'
