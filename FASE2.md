# Fase 2 - Postulacion asistida desde CLI

## Objetivo

Usar el resultado local `output/botjobs_resultados.json` para preparar postulaciones expresamente autorizadas. Toda seleccion de vacantes, CV, cartas y confirmacion de envio debe realizarse mediante comandos y archivos locales.

## Reglas de seguridad

- Ninguna vacante se procesa sin una decision explicita.
- `--dry-run` no modifica archivos ni abre el navegador.
- `--submit` requiere `--browser --confirm-submit ENVIAR`.
- Login, captcha y verificacion humana detienen el flujo.
- Un envio confirmado o incierto no se repite automaticamente.
- Las credenciales permanecen en perfiles locales del navegador y no se versionan.

## Estado actual

El motor `botjobs/apply.py` valida decisiones, CV, cartas, portales soportados e idempotencia. Las decisiones y CV ya se administran mediante los comandos locales `decisions` y `cv`.

## Flujo objetivo

```powershell
python .\bot_jobs.py decisions set --url URL --decision aprobada
python .\bot_jobs.py cv add --file .\mi-cv.pdf
python .\bot_jobs.py --apply-approved --jobs .\output\botjobs_resultados.json --dry-run
python .\bot_jobs.py --apply-approved --jobs .\output\botjobs_resultados.json --browser
```

El comando de envio final solo se usa despues de revisar la evidencia local:

```powershell
python .\bot_jobs.py --apply-approved --jobs .\output\botjobs_resultados.json --browser --submit --confirm-submit ENVIAR
```

Los subcomandos `decisions` y `cv` están disponibles y almacenan sus datos bajo `runtime/`.
