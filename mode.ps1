<#
.SYNOPSIS
    Switch YouTube Transcripter between CPU and GPU.
.EXAMPLE
    .\mode.ps1          # show the current mode
    .\mode.ps1 cpu      # switch to CPU and restart
    .\mode.ps1 gpu      # switch to NVIDIA GPU and restart
#>
[CmdletBinding()]
param(
    [ValidateSet('cpu', 'gpu', 'status')]
    [string]$Mode = 'status'
)

$ErrorActionPreference = 'Stop'

$ProjectDir = $PSScriptRoot
$EnvFile    = Join-Path $ProjectDir '.env'
$CpuValue   = 'docker-compose.yml'
$GpuValue   = 'docker-compose.yml:docker-compose.gpu.yml'

Set-Location $ProjectDir

if (-not (Test-Path $EnvFile)) {
    Write-Host '==> .env not found, creating it from .env.example'
    Copy-Item (Join-Path $ProjectDir '.env.example') $EnvFile
}

function Get-CurrentMode {
    if (Select-String -Path $EnvFile -Pattern '^COMPOSE_FILE=.*gpu' -Quiet) { 'gpu' } else { 'cpu' }
}

if ($Mode -eq 'status') {
    Write-Host "Current mode: $(Get-CurrentMode)"
    Write-Host 'Runtime reported by the app:'
    $probe = "import sys; sys.path.insert(0,'/app'); from app.core import transcriber; print('  ' + transcriber.describe_runtime())"
    docker compose exec -T transcripter python -c $probe 2>$null
    if ($LASTEXITCODE -ne 0) { Write-Host '  (container is not running)' }
    exit 0
}

if ((Get-CurrentMode) -eq $Mode) {
    Write-Host "Already in $Mode mode. Nothing to do."
    exit 0
}

if ($Mode -eq 'gpu') {
    if (-not (Get-Command nvidia-smi -ErrorAction SilentlyContinue)) {
        Write-Warning 'nvidia-smi was not found. You probably do not have an NVIDIA driver installed. See README section 3.'
        $reply = Read-Host 'Continue anyway? [y/N]'
        if ($reply -notmatch '^[Yy]$') { exit 1 }
    }
    Write-Host 'NOTE: the first GPU build downloads about 5 GB of CUDA libraries.'
}

$NewValue = if ($Mode -eq 'gpu') { $GpuValue } else { $CpuValue }

Write-Host "==> Switching to $Mode mode"
$kept = Get-Content $EnvFile | Where-Object {
    $_ -notmatch '^\s*#?\s*(COMPOSE_FILE|COMPOSE_PATH_SEPARATOR)=' -and
    $_ -notmatch '^# Run mode - managed by mode\.' -and
    $_ -notmatch '^#            or docker-compose\.yml'
}
$header = @(
    '# Run mode - managed by mode.ps1. Values: docker-compose.yml',
    '#            or docker-compose.yml:docker-compose.gpu.yml',
    'COMPOSE_PATH_SEPARATOR=:',
    "COMPOSE_FILE=$NewValue"
)
# Write LF-only so the file stays readable by the Linux container tooling.
$content = (($header + $kept) -join "`n") + "`n"
[System.IO.File]::WriteAllText($EnvFile, $content, (New-Object System.Text.UTF8Encoding($false)))

Write-Host '==> Rebuilding and restarting'
docker compose up -d --build

Write-Host ''
Write-Host "Done. Mode is now: $(Get-CurrentMode)"
Write-Host 'Open http://localhost:8501 and check the Runtime line in the sidebar.'
