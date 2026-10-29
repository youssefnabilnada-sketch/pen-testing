# Stops only the isolated aegis-pilot Docker Compose project.
# Preserves all database, Redis and other named volumes and does not touch unrelated containers.
[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location -LiteralPath $repo
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker is not installed.' }
& docker compose --project-name aegis-pilot -f docker-compose.yml -f docker-compose.local-access.yml down --remove-orphans=false
if ($LASTEXITCODE -ne 0) { throw "Docker Compose stop failed (exit code $LASTEXITCODE)." }
Write-Host 'AEGIS local pilot stopped. All data volumes were preserved. Unrelated services were not targeted.' -ForegroundColor Green
