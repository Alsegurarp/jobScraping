# Backend de BotJobs

Este backend expone acciones permitidas de BotJobs mediante FastAPI. No acepta comandos ni rutas desde las solicitudes y nunca usa `shell=True`.

## Instalacion local

Desde la raiz del proyecto:

```powershell
python -m pip install -r .\requirements.txt
```

Para instalar tambien las dependencias de pruebas:

```powershell
python -m pip install -r .\requirements-dev.txt
```

## Iniciar el backend

```powershell
python -m uvicorn backend.main:app --reload
```

La documentacion interactiva queda disponible en `http://127.0.0.1:8000/docs`.

El timeout predeterminado de cada corrida es de 1800 segundos. Puede configurarse antes de iniciar el servidor:

```powershell
$env:BOTJOBS_RUN_TIMEOUT_SECONDS = "3600"
python -m uvicorn backend.main:app --reload
```

## Ejemplos

Salud del servicio:

```bash
curl http://127.0.0.1:8000/health
```

Iniciar busqueda:

```bash
curl -X POST http://127.0.0.1:8000/runs/search \
  -H "Content-Type: application/json" \
  -d '{"portals":["indeed","linkedin"],"max_results":10,"refresh_cache":false,"browser":false,"research":false}'
```

Extraer los links de la plantilla fija:

```bash
curl -X POST http://127.0.0.1:8000/runs/extract-links \
  -H "Content-Type: application/json" \
  -d '{"browser":false,"research":false}'
```

Consultar una corrida y listar las ultimas:

```bash
curl http://127.0.0.1:8000/runs/REEMPLAZAR_CON_RUN_ID
curl "http://127.0.0.1:8000/runs?limit=20"
```

Consultar resultados JSON:

```bash
curl http://127.0.0.1:8000/results/latest
curl http://127.0.0.1:8000/runs/REEMPLAZAR_CON_RUN_ID/results
```

Placeholder de aplicacion, solo en modo simulacion:

```bash
curl -X POST http://127.0.0.1:8000/runs/apply-approved/dry-run
```

El CLI aun no implementa `--apply-approved` ni `--dry-run`. Por ahora esta corrida terminara como `failed` y conservara el error; no aplica ni envia ninguna vacante.

## Estados y archivos

Cada `POST /runs/...` responde con HTTP `202` y un `run_id`. La accion se ejecuta en segundo plano y pasa por `pending`, `running` y finalmente `completed` o `failed`.

Los registros se guardan en `runtime/runs/{run_id}.json`. La carpeta es local y esta excluida de Git. Las corridas se ejecutan de una en una porque actualmente comparten `output/botjobs_resultados.json`.

BotJobs genera JSON directamente desde sus estructuras Python. Al completar una busqueda o extraccion, el backend conserva una copia historica en `runtime/results/{run_id}.json`; ya no existe una conversion intermedia desde Excel. Los endpoints nunca aceptan rutas enviadas por el cliente.

## Seguridad

- Los comandos se construyen internamente como listas de argumentos.
- Los portales estan limitados a Indeed, LinkedIn, OCC, Computrabajo y Glassdoor.
- `max_results` solo acepta valores entre 1 y 50.
- Los cuerpos con propiedades desconocidas se rechazan.
- Perfil, plantilla, salida, script y carpeta de trabajo son rutas internas fijas.
- No existe un endpoint de terminal, comando libre o envio real de aplicaciones.

## Pruebas

```powershell
python -m pytest
```

La separacion entre constructor de comandos, ejecutor y almacenamiento permite sustituir posteriormente la ejecucion local por Redis Queue y los JSON por MongoDB sin cambiar el contrato HTTP.
