# Manual operativo de BotJobs CLI 1.0.0

## Preparacion

Desde PowerShell en la raiz del proyecto:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 -IncludeDev
powershell -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

La instalación crea `.venv`, instala las versiones declaradas en `requirements.lock.txt` y ejecuta `doctor`.

## Operacion diaria

1. Activar el entorno: `.\.venv\Scripts\Activate.ps1`.
2. Ejecutar `python .\bot_jobs.py doctor`.
3. Buscar con un límite pequeño por portal.
4. Revisar `output\botjobs_resultados.json` y las cartas.
5. Agregar o activar el CV con `cv add` y `cv activate`.
6. Registrar decisiones con `decisions set`.
7. Ejecutar primero `--apply-approved --dry-run`.
8. Preparar con `--browser` y revisar evidencia.
9. Usar envío únicamente después de revisar portal, materiales y registro previo.

## Respaldo

```powershell
python .\bot_jobs.py backup create --project . --file .\backups\botjobs.zip
```

Incluye `runtime/`, `cache/` y `output/`. El respaldo se construye temporalmente y reemplaza el archivo anterior solo al completarse.

Restauración:

```powershell
python .\bot_jobs.py backup restore --project . --file .\backups\botjobs.zip --confirm RESTAURAR
```

La restauración sobrescribe los archivos incluidos. Debe ejecutarse con BotJobs y el navegador cerrados.

## Recuperacion

- Corrida interrumpida: ejecutar `doctor` y repetir búsqueda o extracción; la salida JSON anterior se conserva por escritura atómica.
- Envío `en_progreso` o `incierto`: revisar manualmente el portal. No borrar el registro para forzar un reenvío.
- Captcha o login: usar `--login-portal PORTAL`, resolver manualmente y cerrar el navegador.
- Caché problemática: repetir con `--refresh-cache`.
- Resultado perdido: restaurar el respaldo más reciente.
- Dependencia dañada: recrear `.venv` mediante `scripts/install.ps1`.

## Archivos que deben protegerse

- `profile.example.json` o su copia personalizada.
- `runtime/`: CV, decisiones, sesiones y registro de envíos.
- `output/`: resultados, cartas y evidencia referenciada.
- `cache/`: contenido reutilizable y memoria de descartes.

No compartir respaldos sin revisar datos personales y sesiones locales.
