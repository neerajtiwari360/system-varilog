param([int]$Port = 8080)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    foreach ($dockerBin in @((Join-Path $env:ProgramFiles 'Docker\Docker\resources\bin'), (Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin'))) {
        if (Test-Path (Join-Path $dockerBin 'docker.exe')) { $env:PATH = "$dockerBin;$env:PATH"; break }
    }
}
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker is missing from PATH. Install/start Docker Desktop with Linux containers and reopen PowerShell.'
}
docker info --format '{{.ServerVersion}}'
if ($LASTEXITCODE -ne 0) { throw 'Docker Desktop is not ready.' }
if (Get-Command uv -ErrorAction SilentlyContinue) {
    $env:UV_CACHE_DIR = Join-Path $PSScriptRoot '.uv-cache'
    if (-not (Test-Path '.venv\Scripts\python.exe')) {
        uv venv --python 3.12
        if ($LASTEXITCODE -ne 0) { throw 'Could not create Python environment.' }
    }
    uv pip install --python .venv/Scripts/python.exe -e .
} else {
    if (-not (Test-Path '.venv\Scripts\python.exe')) {
        py -3 -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Python 3.11+ or uv is required.' }
    }
    & .venv/Scripts/python.exe -m pip install -e .
}
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
docker compose build sim wave
if ($LASTEXITCODE -ne 0) { throw 'Tool image build failed.' }
$env:SV_STUDIO_PORT = "$Port"
Write-Host "SV Studio: http://127.0.0.1:$Port"
& .venv/Scripts/python.exe -m sv_studio.app
