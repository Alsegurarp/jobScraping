param(
    [string]$Python = ".\.venv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    & $Python -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw "La suite de pruebas fallo (codigo $LASTEXITCODE)" }
    & $Python .\bot_jobs.py doctor
    if ($LASTEXITCODE -ne 0) { throw "El diagnostico fallo (codigo $LASTEXITCODE)" }
    & $Python .\bot_jobs.py --demo
    if ($LASTEXITCODE -ne 0) { throw "La demo fallo (codigo $LASTEXITCODE)" }
    Write-Host "Verificacion BotJobs completada"
} finally {
    Pop-Location
}
