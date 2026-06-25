# BotJobs

Herramienta local personal para filtrar vacantes tech Junior, priorizar las mejores opciones y generar materiales de aplicacion.

## Fase 1A

Entrada:

- `vacantes.template.xlsx`: pega aqui links/vacantes copiadas desde Indeed, LinkedIn, OCC, Computrabajo o Glassdoor.
- `profile.example.json`: perfil base de Rene Alexis Segura Perez, filtros laborales y criterios de ranking.

Salida:

- `output/botjobs_resultados.xlsx`
  - `vacantes_detectadas`
  - `preseleccionadas`
  - `descartadas`
  - `aplicadas`
  - `empresas_investigadas`
- `output/cartas/*.md`: carta personalizada por vacante.

## Crear plantilla

```powershell
C:\Users\alseg\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe .\bot_jobs.py --create-template --jobs .\vacantes.template.xlsx
```

## Ejecutar sin internet

```powershell
C:\Users\alseg\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe .\bot_jobs.py --profile .\profile.example.json --jobs .\vacantes.template.xlsx --out .\output
```

## Ejecutar con investigacion web

```powershell
C:\Users\alseg\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe .\bot_jobs.py --profile .\profile.example.json --jobs .\vacantes.template.xlsx --out .\output --research
```

## Chequeo rapido

```powershell
C:\Users\alseg\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe .\bot_jobs.py --demo
```

## Criterios actuales

- Salario minimo: 20,000 MXN mensuales.
- Si no hay salario publicado: la carta menciona interes si supera 22,000 MXN mensuales o equivalente en USD.
- Presencial/hibrido: solo CDMX.
- Remoto: Mexico, LATAM, USA, Espana y UK.
- Industrias permitidas: consultoras, e-commerce, logistica, SaaS y fintech.
- Industrias bloqueadas: seguridad, viajes, travel y turismo.
- Excluir: trabajos por proyecto, mas de 40 horas, guardias, nocturno, fines de semana, 24/7, alta disponibilidad y seniority alto.
- Fase 1A no auto-aplica. Prepara compendio, ranking, investigacion y cartas.
