# AEGIS local development pilot for Windows
# Runs only the repository's LOCAL Docker Compose configuration.
# Does not configure cloud networking, public tunnels, or production customer access.
[CmdletBinding()]
param(
    [switch]$StatusOnly
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location -LiteralPath $repo

function Invoke-Compose {
    param([string[]]$ComposeArgs)
    & docker compose --project-name aegis-pilot -f docker-compose.yml -f docker-compose.local-access.yml @ComposeArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose failed (exit code $LASTEXITCODE). Previous data volumes have NOT been deleted."
    }
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker Desktop was not found. Install Docker Desktop for Windows with WSL 2 from the official Docker website, then restart your terminal.'
}
& docker info --format '{{.ServerVersion}}' 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw 'Docker Desktop is not running, or the engine is unavailable. Open Docker Desktop first.'
}
& docker compose version | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Docker Compose v2 is required.' }

if ($StatusOnly) {
    Invoke-Compose -ComposeArgs @('ps')
    exit 0
}

$envPath = Join-Path $repo '.env'
if (-not (Test-Path -LiteralPath $envPath)) {
    $bytes = New-Object byte[] 32
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    $password = -join ($bytes | ForEach-Object { $_.ToString('x2') })
    $lines = @(
        '# Generated only for isolated local AEGIS testing. Never commit or share this file.',
        "POSTGRES_PASSWORD=$password",
        'WEB_ORIGIN=http://localhost:3000',
        'COOKIE_SECURE=false',
        'LOCAL_FIXTURE_MODE=true',
        'PAYMENTS_ENABLED=false',
        'PRICING_ENABLED=false',
        'BILLING_MODE=disabled',
        'DEMO_ACCESS_ENABLED=true',
        'FIREBASE_AUTH_ENABLED=false',
        'AI_ASSISTANT_ENABLED=false',
        'AI_PROVIDER_ENABLED=false',
        'GITHUB_ENABLED=false'
    )
    [IO.File]::WriteAllLines($envPath, $lines, (New-Object System.Text.UTF8Encoding($false)))
    Write-Host 'Created local .env with a random database password. Do not upload or share it.' -ForegroundColor Green
} else {
    $raw = Get-Content -Raw -LiteralPath $envPath
    if ($raw -notmatch '(?m)^WEB_ORIGIN=http://localhost:3000\s*$' -or
        $raw -notmatch '(?m)^LOCAL_FIXTURE_MODE=true\s*$' -or
        $raw -notmatch '(?m)^COOKIE_SECURE=false\s*$') {
        throw 'Existing .env is not explicitly configured for isolated local testing. Refusing to reuse possibly production settings.'
    }
    if ($raw -match 'replace-with-a-long-random-local-password' -or
        $raw -notmatch '(?m)^POSTGRES_PASSWORD=[0-9a-f]{40,}\s*$') {
        throw 'Existing .env password is missing or nonstandard. Keep your existing database password; do not overwrite it. Configure a safe local test .env manually.'
    }
    Write-Host 'Using existing explicitly local .env; no secrets will be displayed.' -ForegroundColor Cyan
}

Write-Host 'Starting local PostgreSQL, Redis, test mail service, and isolated fixture...' -ForegroundColor Cyan
Invoke-Compose -ComposeArgs @('up','--build','-d','db','redis','mailpit','fixture')
Write-Host 'Applying database migrations (no volume reset)...' -ForegroundColor Cyan
Invoke-Compose -ComposeArgs @('run','--rm','migrate')
Write-Host 'Starting API, web, scanner, intelligence and scheduler...' -ForegroundColor Cyan
Invoke-Compose -ComposeArgs @('up','--build','-d','api','web','worker','intelligence-worker','scheduler')

$healthy = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $reply = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 4
        if ($reply.StatusCode -eq 200) { $healthy = $true; break }
    } catch {
        Start-Sleep -Seconds 3
    }
}
Invoke-Compose -ComposeArgs @('ps')
if (-not $healthy) {
    Write-Warning 'Local API did not pass its health check. Check the logs with: docker compose --project-name aegis-pilot -f docker-compose.yml -f docker-compose.local-access.yml logs --tail=80 api'
    throw 'AEGIS local pilot started, but API health is not confirmed. Do not expose any service publicly.'
}
Write-Host 'AEGIS LOCAL API health check passed.' -ForegroundColor Green
Write-Host 'Website (local): http://localhost:3000'
Write-Host 'API (local): http://127.0.0.1:8000/health'
Write-Host 'Mailpit test mailbox (local): http://localhost:8025'
Write-Host 'Vercel is NOT connected to this local pilot; public customer traffic remains DISABLED.'
