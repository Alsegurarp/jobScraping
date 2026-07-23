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
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

La documentacion interactiva queda disponible en `http://127.0.0.1:8000/docs`.

## Ejecutar con Docker

```powershell
docker compose up --build
```

El servicio queda disponible en `http://localhost:8000`. Los resultados, documentos, decisiones y caché se conservan en volúmenes de Docker.

Para conectar la app móvil a un despliegue remoto, configura `EXPO_PUBLIC_API_URL` y `EXPO_PUBLIC_API_KEY` y reinicia Expo.

## Desplegar en Vercel

Configuración del proyecto:

- Root Directory: raíz del repositorio (`.`).
- Framework Preset: FastAPI o detección automática.
- Entrada detectada: `app.py`.
- No configurar Build Command, Output Directory ni Install Command.

En la pestaña Storage de Vercel, crea un Blob **privado** y conéctalo al proyecto. Vercel agregará `BLOB_READ_WRITE_TOKEN`.

Declara estas variables para Production y Preview:

```text
BOTJOBS_API_KEY=una-clave-aleatoria-larga
BOTJOBS_RUN_TIMEOUT_SECONDS=300
```

`VERCEL` y `PORT` son variables proporcionadas por la plataforma y no deben declararse manualmente.

El despliegue guarda `runtime`, `output` y `cache` como un snapshot en el Blob privado. Las ejecuciones se realizan de forma síncrona para terminar dentro de la solicitud de Vercel. Este modo está diseñado para un solo usuario y una ejecución a la vez.

Después del despliegue, configura la app móvil:

```text
EXPO_PUBLIC_API_URL=https://TU-PROYECTO.vercel.app
EXPO_PUBLIC_API_KEY=la-misma-clave-de-BOTJOBS_API_KEY
```

Vercel limita las solicitudes a 4.5 MB; BotJobs limita cada CV PDF a 4 MB.

El timeout predeterminado de cada corrida es de 1800 segundos. Puede configurarse antes de iniciar el servidor:

```powershell
$env:BOTJOBS_RUN_TIMEOUT_SECONDS = "3600"
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
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

Consultar una carta por su identificador:

```bash
curl http://127.0.0.1:8000/letters/REEMPLAZAR_CON_CARTA_ID
```

Guardar decision manual por vacante:

```bash
curl -X POST http://127.0.0.1:8000/jobs/decision -H "Content-Type: application/json" -d "{\"url\":\"https://example.com/job\",\"decision\":\"aprobada\"}"
```

Decisiones validas: `aprobada`, `descartada`, `revision`. Se guardan localmente en `runtime/decisions.json` y se mezclan al consultar resultados.

Subir, listar y consultar CV:

```bash
curl -X POST "http://127.0.0.1:8000/documents/cv?filename=Rene_Alexis_Segura_CV.pdf" -H "Content-Type: application/pdf" --data-binary "@Rene_Alexis_Segura_CV.pdf"
curl http://127.0.0.1:8000/documents/cv
curl -X POST http://127.0.0.1:8000/documents/cv/REEMPLAZAR_CON_CV_ID/active
curl http://127.0.0.1:8000/documents/cv/REEMPLAZAR_CON_CV_ID
```

Los CV se validan como PDF, tienen un limite de 10 MB, uno queda marcado como activo y permanecen en `runtime/documents/cv/`.

Placeholder de aplicacion, solo en modo simulacion:

```bash
curl -X POST http://127.0.0.1:8000/runs/apply-approved/dry-run
```

El CLI valida decisiones aprobadas, CV activo y carta sin abrir el navegador ni modificar resultados.

Para preparar formularios compatibles y guardar evidencia, sin enviar:

```bash
curl -X POST http://127.0.0.1:8000/runs/apply-approved/prepare
```

Reintentar solo aplicaciones en intervención:

```bash
curl -X POST http://127.0.0.1:8000/runs/apply-approved/retry
```

Enviar aplicaciones aprobadas con confirmación explícita:

```bash
curl -X POST http://127.0.0.1:8000/runs/apply-approved/submit -H "Content-Type: application/json" -d "{\"confirmation\":\"ENVIAR\"}"
```

El envío se bloquea para dominios no soportados, materiales faltantes y vacantes con un envío previo confirmado o incierto.

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
