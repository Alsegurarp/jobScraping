# BotJobs

Herramienta local personal para buscar vacantes tech Junior, entrar a portales laborales, extraer descripciones, filtrar oportunidades y generar materiales de aplicacion.

## Objetivo principal

BotJobs debe evitar perder tiempo aplicando a ofertas laborales irrelevantes. Para eso, el flujo central debe funcionar de forma automatizada:

- Buscar vacantes automaticamente en Indeed, LinkedIn, OCC, Computrabajo y Glassdoor.
- Entrar a los portales laborales para consultar los resultados.
- Extraer descripciones, empresa, ubicacion, modalidad, salario, fecha, link y correo de contacto cuando exista.
- Filtrar ofertas recientes, idealmente no mayores a 2 semanas.
- Rankear vacantes segun el perfil y criterios laborales definidos.
- Generar un compendio en `.xlsx` y cartas personalizadas en `.md` solo para vacantes preseleccionadas.

Si un portal presenta login, captcha, verificacion humana o bloqueo normal de plataforma, el bot debe detenerse, avisar al usuario y continuar despues de la intervencion manual.

## Fase actual

Entrada:

- Busqueda automatica en Indeed, LinkedIn, OCC, Computrabajo y Glassdoor.
- Extraccion automatica desde links de vacantes.
- `vacantes.template.xlsx`: respaldo manual para pegar links/vacantes y validar ranking, cartas e investigacion cuando un portal bloquee o cambie su estructura.
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
python .\bot_jobs.py --create-template --jobs .\vacantes.template.xlsx
```

## Ejecutar sin internet

```powershell
python .\bot_jobs.py --profile .\profile.example.json --jobs .\vacantes.template.xlsx --out .\output
```

## Ejecutar con investigacion web

```powershell
python .\bot_jobs.py --profile .\profile.example.json --jobs .\vacantes.template.xlsx --out .\output --research
```

## Extraer datos desde links

Abre los links colocados en la columna `url` del `.xlsx`, intenta extraer titulo, portal, descripcion y correo de contacto, y despues ejecuta ranking/cartas.

```powershell
python .\bot_jobs.py --profile .\profile.example.json --jobs .\vacantes.template.xlsx --out .\output --extract-links
```

Tambien puede combinarse con investigacion web de empresas:

```powershell
python .\bot_jobs.py --profile .\profile.example.json --jobs .\vacantes.template.xlsx --out .\output --extract-links --research
```

Estado actual: `--extract-links` usa un extractor generico de HTML. Si una pagina requiere JavaScript, login, captcha o bloquea el acceso, la vacante queda marcada con `requiere_intervencion` y `estado_extraccion`.

## Extraer links con navegador automatizado

Usa Playwright desde el runtime local cuando una pagina necesita renderizado de navegador. Este modo sigue sin resolver captchas ni logins por su cuenta: si detecta una barrera, marca la vacante para intervencion manual.

```powershell
python .\bot_jobs.py --profile .\profile.example.json --jobs .\vacantes.template.xlsx --out .\output --extract-links --browser
```

Si el entorno bloquea la apertura de Chrome/Edge, el resultado queda marcado como `estado_extraccion=navegador_bloqueado`. En ese caso, ejecuta el comando desde una terminal local normal.

## Ejecutar busqueda automatica

Busca vacantes en portales soportados, deduplica links candidatos, extrae detalles y ejecuta ranking/cartas.

```powershell
python .\bot_jobs.py --auto-search --profile .\profile.example.json --out .\output --max-results 25
```

Para probar un portal concreto con pocos resultados:

```powershell
python .\bot_jobs.py --auto-search --profile .\profile.example.json --out .\output --portals indeed --max-results 5
```

Portales aceptados en `--portals`: `indeed`, `linkedin`, `occ`, `computrabajo`, `glassdoor`.

Estado actual: `--auto-search` usa paginas de resultados publicas y extrae links candidatos. Si un portal bloquea, cambia su estructura o no muestra resultados publicos, puede devolver pocos resultados o ninguno. Los links encontrados pasan por los extractores del paso 5.

## Roadmap del nucleo

1. Normalizar el contrato de datos de vacantes para que Excel, links y portales usen la misma estructura interna.
2. Separar el script en modulos: perfil, ranking, workbook, cartas, investigacion y portales.
3. Crear modo `--extract-links` para abrir links pegados en el `.xlsx` y extraer datos de cada vacante. Estado: implementado con extractor generico.
4. Agregar navegador automatizado para abrir paginas reales y detectar captcha, login o bloqueo. Estado: implementado como `--extract-links --browser`.
5. Implementar extractores por portal, uno por uno: Indeed, Computrabajo, OCC, Glassdoor y LinkedIn. Estado: implementacion inicial completa para links de vacantes.
6. Crear modo `--auto-search` para buscar vacantes automaticamente en los portales soportados. Estado: implementado en version inicial.
7. Agregar cache local de HTML/texto extraido para evitar repetir navegacion innecesaria.
8. Registrar estados de extraccion: `ok`, `captcha`, `login_requerido`, `bloqueado`, `estructura_no_reconocida`, `sin_descripcion` y `error_red`.
9. Mejorar ranking con datos reales: industria, seniority, salario, modalidad, spam y trabajos por proyecto.
10. Generar workbook operativo con hojas de detectadas, preseleccionadas, descartadas, requiere intervencion, empresas investigadas y aplicadas.
11. Agregar reporte de ejecucion con conteos de detectadas, extraidas, preseleccionadas, descartadas, intervenciones y cartas.
12. Probar primero con Indeed en una busqueda pequena de maximo 10 resultados.
13. Expandir portal por portal sin agregar uno nuevo hasta que el anterior extraiga y falle de forma controlada.
14. Mantener README actualizado con estado real de soporte por portal y comandos disponibles.

## Contrato de datos de vacante

Todas las fuentes deben transformarse a estos campos antes de rankear o generar cartas:

- `titulo`
- `empresa`
- `portal`
- `url`
- `descripcion`
- `ubicacion`
- `modalidad`
- `salario`
- `fecha_publicacion`
- `email_contacto`
- `industria_detectada`
- `fuente_extraccion`
- `requiere_intervencion`
- `estado_extraccion`
- `horas_semana`
- `seniority`
- `idioma`
- `url_empresa`

## Estructura del proyecto

- `bot_jobs.py`: entrada principal compatible con los comandos actuales.
- `botjobs/app.py`: orquestacion del flujo local.
- `botjobs/schema.py`: contrato de datos de vacantes y aliases de columnas antiguas.
- `botjobs/profile.py`: carga del perfil.
- `botjobs/ranking.py`: filtros, scoring, fechas, salario, modalidad e idioma.
- `botjobs/workbook.py`: lectura y escritura de archivos `.xlsx`.
- `botjobs/letters.py`: cartas y mensajes cortos para reclutadores.
- `botjobs/research.py`: investigacion web de empresas.
- `botjobs/search.py`: busqueda automatica de links candidatos en portales.
- `botjobs/extractors.py`: extraccion generica de datos desde links.
- `botjobs/browser.py`: extraccion con navegador automatizado.
- `botjobs/browser_extract.mjs`: script Playwright usado por el extractor de navegador.
- `botjobs/extractor_utils.py`: utilidades compartidas para extractores HTML.
- `botjobs/portals/`: extractores especificos por portal.
- `botjobs/utils.py`: utilidades compartidas.

## Soporte por portal

- Indeed: extractor inicial para links de vacantes.
- Computrabajo: extractor inicial para links de vacantes.
- OCC: extractor inicial para links de vacantes.
- Glassdoor: extractor inicial para links de vacantes.
- LinkedIn: extractor inicial para links de vacantes.

Todos los extractores intentan leer JSON-LD `JobPosting`, titulo, empresa, ubicacion, salario, fecha, descripcion y correo visible. Si el portal no expone esos datos o bloquea la pagina, el flujo cae a metadatos/texto visible o marca `estado_extraccion`.

## Chequeo rapido

```powershell
python .\bot_jobs.py --demo
```

## Configuracion local

Las rutas especificas de cada maquina deben documentarse en `READMElocal.md`.
Ese archivo no se versiona y esta incluido en `.gitignore`.

## Criterios actuales

- Salario minimo: 20,000 MXN mensuales.
- Si no hay salario publicado: la carta menciona interes si supera 22,000 MXN mensuales o equivalente en USD.
- Presencial/hibrido: solo CDMX.
- Remoto: Mexico, LATAM, USA, Espana y UK.
- Industrias permitidas: consultoras, e-commerce, logistica, SaaS y fintech.
- Industrias bloqueadas: seguridad, viajes, travel y turismo.
- Excluir: trabajos por proyecto, mas de 40 horas, guardias, nocturno, fines de semana, 24/7, alta disponibilidad y seniority alto.
- Fase 1A no auto-aplica. Prepara compendio, ranking, investigacion y cartas.
- Las vacantes con `estado=descartada` no generan carta ni mensaje para evitar gasto de recursos.

## Futuras implementaciones

- Aplicar automaticamente a vacantes.
- Enviar emails a reclutadores.
- Usar IA para redactar cartas mas inteligentes; por ahora usa plantillas simples.
- Actualizar Google Sheets directamente.
- Validar visualmente o sincronizar el Excel subido a Google Sheets.
