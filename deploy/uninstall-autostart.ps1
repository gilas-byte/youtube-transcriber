<#
.SYNOPSIS
    Windows only. Removes the logon Scheduled Task. Container and data stay.
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\deploy\uninstall-autostart.ps1
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$TaskName = 'YouTubeTranscripter'

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed the '$TaskName' scheduled task."
} else {
    Write-Host "No '$TaskName' scheduled task found. Nothing to do."
}

Write-Host ''
Write-Host 'NOTE: the container still has restart:unless-stopped, so Docker will keep'
Write-Host 'bringing it back. To stop that too, run:  docker compose down'
