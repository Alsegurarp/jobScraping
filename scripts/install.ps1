param(
    [string]$Python = "python",
    [string]$Venv = ".venv",
    [switch]$IncludeDev
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $projectRoot $Venv
& $Python -m venv $venvPath
if ($LASTEXITCODE -ne 0) { throw "No se pudo crear el entorno virtual (codigo $LASTEXITCODE)" }
$venvPython = Join-Path $venvPath "Scripts\python.exe"
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "No se pudo preparar pip (codigo $LASTEXITCODE)" }
& $venvPython -m pip install -r (Join-Path $projectRoot "requirements.lock.txt")
if ($LASTEXITCODE -ne 0) { throw "No se pudieron instalar dependencias (codigo $LASTEXITCODE)" }
if ($IncludeDev) {
    & $venvPython -m pip install -r (Join-Path $projectRoot "requirements-dev.txt")
    if ($LASTEXITCODE -ne 0) { throw "No se pudieron instalar dependencias de prueba (codigo $LASTEXITCODE)" }
}
& $venvPython (Join-Path $projectRoot "bot_jobs.py") doctor
if ($LASTEXITCODE -ne 0) { throw "El diagnostico de BotJobs fallo (codigo $LASTEXITCODE)" }
Write-Host "BotJobs instalado en $venvPath"
