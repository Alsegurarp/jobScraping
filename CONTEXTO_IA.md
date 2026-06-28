# Contexto para planeacion de arquitectura - BotJobs

Este documento esta pensado para compartirse con una IA de planeacion, junto con `README.md` y `FASE2.md`. No es una guia de uso final; es un resumen amplio del contexto, decisiones, restricciones y estado real del proyecto para planear arquitectura e integraciones futuras.

## Resumen ejecutivo

BotJobs es una herramienta local y personal para reducir tiempo perdido en busqueda y aplicacion a vacantes laborales. El objetivo es que el sistema busque vacantes en portales definidos, extraiga informacion, evalue si una vacante encaja con el perfil de Rene Alexis Segura Perez, genere materiales personalizados y, en una fase futura, prepare o ejecute aplicaciones solo con autorizacion explicita.

El proyecto esta en una Fase 1 funcional: genera resultados JSON para el backend y la app movil, rankea vacantes, guarda descartes, genera cartas `.md` para vacantes preseleccionadas y registra cuando un portal requiere intervencion humana. La Fase 2 esta planeada en `FASE2.md` y se enfoca en documentos dentro de la app y aplicacion asistida/controlada.

## Usuario y caso de uso

Usuario principal:

- Nombre: Rene Alexis Segura Perez.
- Uso: personal.
- Perfil profesional objetivo: tech, principalmente roles Junior.
- Idiomas: espanol e ingles.
- CV principal local: `Rene_Alexis_Segura_CV.pdf`.
- GitHub principal indicado: `github.com/Alsegurarp`.
- GitHub adicional indicado: `alexis-perez-webp`.

Caso de uso:

- Evitar perder tiempo aplicando a ofertas malas, falsas, irrelevantes o incompatibles.
- Encontrar vacantes recientes y relevantes.
- Priorizar vacantes por ajuste al perfil.
- Generar cartas de presentacion y mensajes cortos al reclutador.
- Guardar trazabilidad de que vacantes se detectaron, cuales se descartaron, cuales requieren intervencion y cuales serian candidatas para aplicar.
- En el futuro, aplicar a vacantes despues de autorizacion del usuario.

## Objetivo del producto

Construir un bot local de busqueda laboral con maxima automatizacion posible, manteniendo control humano en puntos sensibles:

- No aplicar sin autorizacion.
- No resolver captchas ni evadir controles de plataforma.
- No enviar emails sin autorizacion.
- Mantener datos sensibles localmente.
- Registrar todo en archivos locales.

El producto no es una plataforma SaaS. Actualmente tiene CLI, backend FastAPI y app Expo/React Native, todos locales. Debe permanecer simple pero expansible.

## Portales objetivo

Portales priorizados:

1. Indeed
2. LinkedIn
3. OCC
4. Computrabajo
5. Glassdoor

Otros portales no interesan por ahora.

Estado actual por portal:

- Indeed: encuentra links candidatos; algunas paginas de detalle pueden bloquear y quedar en intervencion.
- LinkedIn: extrae ofertas reales desde `/jobs/view`; se filtro para evitar links internos de busqueda como `#main-content`.
- OCC: la busqueda publica puede responder HTTP 403; el sistema lo registra como `bloqueado`, `requiere_intervencion=si`, `ignorar_en_futuro=no`.
- Computrabajo: la busqueda publica puede bloquear; se registra como intervencion, no como descarte permanente.
- Glassdoor: extrae ofertas reales desde `job-listing` y `partner/jobListing`; se filtro para evitar links de navegacion.

## Criterios de busqueda y perfil

Criterios actuales del usuario:

- Salario minimo aceptable: $20,000 MXN mensuales o equivalente en USD.
- Si la vacante no publica salario, la carta puede mencionar interes si supera $22,000 MXN mensuales o equivalente en USD.
- Ubicacion presencial: solo CDMX.
- Remoto: Mexico, LATAM, USA, Espana y UK.
- Idiomas: aceptar ofertas 100% en ingles o espanol.
- Seniority objetivo: Junior.
- Industrias preferidas: consultoras, e-commerce, logistica, SaaS, fintech.
- Industrias o dominios a evitar: seguridad, viajes, travel, turismo.
- Excluir trabajos por proyecto.
- Prioridad de contratacion: nomina/tiempo completo, pero acepta freelance si no prohibe tener otros empleos adicionales.
- Disponibilidad: 4 semanas despues de recibir contrato.
- No aplicar a ofertas de mas de 40 horas laborales.
- Priorizar remoto e hibrido.
- Tono de cartas: formal, enfocado a reclutadores tech.
- Idioma de carta: idioma de la vacante.

Orden declarado de importancia para criterios:

1. Industria
2. Salario
3. Horario
4. Remoto
5. Ubicacion
6. Seniority
7. Skills

## Fase 1: lo que ya existe

La Fase 1 ya produce un compendio local con busqueda, extraccion, ranking y cartas.

Capacidades implementadas:

- CLI principal en `bot_jobs.py`.
- Busqueda automatica con `--auto-search`.
- Seleccion de portales con `--portals`.
- Limite de resultados con `--max-results`.
- Extraccion desde links pegados en Excel con `--extract-links`.
- Modo navegador con `--browser`.
- Cache local con `--refresh-cache` y TTL configurable.
- Investigacion basica con `--research`.
- Creacion de plantilla con `--create-template`.
- Modo demo con `--demo`.
- Salida `.json` directa, sin conversion intermedia desde Excel.
- Cartas `.md` para vacantes preseleccionadas.
- Memoria de URLs descartadas en `cache/ignored_urls.json`.

Comandos clave actuales:

```powershell
python .\bot_jobs.py --auto-search --profile .\profile.example.json --out .\output --max-results 25
```

```powershell
python .\bot_jobs.py --auto-search --profile .\profile.example.json --out .\output --portals indeed,linkedin --max-results 10 --refresh-cache
```

```powershell
python .\bot_jobs.py --profile .\profile.example.json --jobs .\vacantes.template.xlsx --out .\output --extract-links
```

```powershell
python .\bot_jobs.py --profile .\profile.example.json --jobs .\vacantes.template.xlsx --out .\output --extract-links --browser
```

## Salida actual del sistema

Archivo principal:

- `output/botjobs_resultados.json`

Secciones actuales:

- `resumen_ejecucion`
- `vacantes_detectadas`
- `preseleccionadas`
- `descartadas`
- `aplicadas`
- `requiere_intervencion`
- `empresas_investigadas`

Cartas:

- `output/cartas/*.md`

El sistema no genera cartas para vacantes descartadas. Esto fue una decision explicita para evitar gasto de recursos y ruido.

## Contrato de datos actual

Campos principales de vacante:

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
- `ignorar_en_futuro`
- `cache_hit`
- `motivo_intervencion`
- `accion_recomendada`
- `horas_semana`
- `seniority`
- `idioma`
- `url_empresa`

Campos de salida adicionales:

- `prioridad`
- `score`
- `estado`
- `nombre_de_la_vacante`
- `documento_que_se_manda`
- `carta_de_interes_al_rol`
- `mensaje_corto_reclutador`
- `razon_menos_250`
- `matched_skills`
- `flags`

Estados relevantes:

- `preseleccionada`
- `descartada`
- `requiere_intervencion=si/no`
- `estado_extraccion=ok`
- `estado_extraccion=captcha`
- `estado_extraccion=login_requerido`
- `estado_extraccion=bloqueado`
- `estado_extraccion=navegador_bloqueado`
- `estado_extraccion=estructura_no_reconocida`
- `estado_extraccion=sin_descripcion`
- `estado_extraccion=error_red`
- `estado_extraccion=ignorada_previamente`

Regla importante:

- Vacantes descartadas normales se marcan con `ignorar_en_futuro=si`.
- Busquedas bloqueadas o filas que requieren intervencion manual no se marcan como `ignorar_en_futuro`, aunque queden descartadas por filtros. Deben poder reintentarse.

## Arquitectura actual

Estructura principal:

```text
bot_jobs.py
botjobs/
  app.py
  browser.py
  browser_extract.mjs
  cache.py
  extractor_utils.py
  extractors.py
  letters.py
  profile.py
  ranking.py
  research.py
  schema.py
  search.py
  utils.py
  workbook.py
  portals/
    common.py
    computrabajo.py
    glassdoor.py
    indeed.py
    linkedin.py
    occ.py
```

Responsabilidades conocidas:

- `bot_jobs.py`: wrapper de entrada.
- `botjobs/app.py`: orquestacion CLI.
- `botjobs/schema.py`: contrato y normalizacion.
- `botjobs/profile.py`: carga del perfil.
- `botjobs/ranking.py`: scoring, filtros, inferencias.
- `botjobs/workbook.py`: lectura de la plantilla manual `.xlsx`.
- `botjobs/results.py`: escritura directa de resultados JSON.
- `botjobs/letters.py`: cartas y mensajes cortos.
- `botjobs/research.py`: investigacion basica de empresa.
- `botjobs/search.py`: busqueda automatica de links candidatos.
- `botjobs/cache.py`: cache HTML bruto y memoria de ignoradas.
- `botjobs/extractors.py`: enruta extraccion por link.
- `botjobs/extractor_utils.py`: fetch, HTML, JSON-LD, detecciones.
- `botjobs/browser.py`: integracion con navegador automatizado.
- `botjobs/browser_extract.mjs`: script Playwright.
- `botjobs/portals/*`: extractores por portal.

## Decisiones tecnicas actuales

- Herramienta local, no SaaS.
- Python como runtime principal.
- `openpyxl` para Excel.
- Playwright/Node para navegador automatizado cuando se usa `--browser`.
- Cache local en carpeta `cache/`.
- No se guarda texto limpio en cache; solo HTML bruto.
- TTL de cache: 120 horas.
- Output canonico en `.json` para FastAPI y React Native.
- `READMElocal.md` contiene rutas locales y no se sube al repo.
- Datos sensibles deben permanecer locales.
- No se usa IA en la ejecucion actual; las cartas son plantillas simples.

## Seguridad, privacidad y restricciones

Restricciones del usuario:

- Manejar datos sensibles localmente.
- Aplicar solo despues de autorizacion al leer las vacantes filtradas.
- No construir sistema de evasion de captchas.
- Si aparece captcha/login/verificacion, el usuario puede intervenir manualmente.
- Continuar con automatizacion de aplicacion en el futuro, pero con control humano y autorizacion.

Restricciones tecnicas actuales:

- Portales pueden bloquear scraping.
- El navegador puede estar bloqueado por el entorno donde se ejecuta.
- Algunas paginas tienen estructura cambiante.
- No hay sincronizacion directa con Google Sheets.
- No hay pruebas automatizadas formales todavia.

## Fase 2 planeada

La Fase 2 debe convertir el compendio en un flujo de aplicacion asistida.

Principio central:

- Ninguna vacante se envia sin autorizacion explicita.

Idea de flujo:

1. Ejecutar Fase 1.
2. Revisar `preseleccionadas`.
3. Marcar `autorizar_aplicacion=si`.
4. Ejecutar dry-run.
5. Ejecutar navegador asistido.
6. Preparar formularios.
7. Detenerse antes de enviar, salvo que exista bandera explicita `--submit`.
8. Registrar resultado.

Comandos propuestos:

```powershell
python .\bot_jobs.py --apply-approved --profile .\profile.example.json --jobs .\output\botjobs_resultados.json --dry-run
```

```powershell
python .\bot_jobs.py --apply-approved --profile .\profile.example.json --jobs .\output\botjobs_resultados.json --browser
```

```powershell
python .\bot_jobs.py --apply-approved --profile .\profile.example.json --jobs .\output\botjobs_resultados.json --browser --submit
```

Columnas propuestas para Fase 2:

- `autorizar_aplicacion`
- `estado_aplicacion`
- `fecha_aplicacion`
- `portal_aplicacion`
- `cv_usado`
- `carta_usada`
- `mensaje_usado`
- `requiere_confirmacion_envio`
- `resultado_aplicacion`
- `evidencia_aplicacion`
- `notas_aplicacion`

Estados propuestos de aplicacion:

- `pendiente`
- `autorizada`
- `preparada`
- `aplicada`
- `fallida`
- `requiere_intervencion`
- `omitida`

Arquitectura propuesta para Fase 2:

```text
botjobs/apply/
  __init__.py
  common.py
  runner.py
  indeed.py
  linkedin.py
  occ.py
  computrabajo.py
  glassdoor.py
```

## Preguntas utiles para planear con IA

Preguntas de arquitectura:

- Conviene mantener CLI puro o agregar una UI local ligera?
- Como versionar y migrar el contrato JSON sin perder historial?
- Como disenar un sistema de estados de aplicacion que no pierda historial?
- Como separar scraping, ranking, generacion de materiales y aplicacion en componentes mantenibles?
- Como modelar errores por portal sin llenar el codigo de casos especiales?
- Como manejar sesiones persistentes sin exponer credenciales?
- Como asociar `cv_id` y `carta_id` sin exponer rutas locales?

Preguntas de integraciones:

- Cual seria la mejor forma de integrar Google Sheets sin romper el modo local?
- Como agregar IA para cartas mejores sin enviar datos sensibles de mas?
- Como usar IA para detectar vacantes falsas, spam o baja calidad?
- Como registrar evidencia de aplicacion: screenshots, HTML, URL final, timestamps?
- Como disenar reintentos manuales despues de captcha/login?

Preguntas de producto:

- Que acciones deben requerir confirmacion humana obligatoria?
- Como evitar aplicaciones accidentales?
- Que nivel de automatizacion es aceptable para portales con formularios largos?
- Como priorizar portales para Fase 2?
- Como medir si el sistema realmente ahorra tiempo?

## Recomendacion de roadmap futuro

Roadmap sugerido despues de Fase 1:

1. Congelar contrato actual de Fase 1.
2. Agregar pruebas basicas para ranking, resultados y extractores.
3. Implementar la vista `Documentos` para subir y consultar CV y cartas.
4. Implementar `--apply-approved --dry-run`.
5. Implementar modulo `botjobs/apply`.
6. Implementar un portal en modo asistido, probablemente LinkedIn o Glassdoor.
7. Registrar evidencia de intentos.
8. Agregar sesiones persistentes manuales.
9. Agregar `--submit` solo despues de varias pruebas.
10. Integrar IA para mejorar cartas.
11. Integrar Google Sheets.
12. Agregar aprendizaje de descartes, spam y empresas bloqueadas.

## Riesgos conocidos

- Bloqueos por portal.
- Cambios de estructura HTML.
- Formularios con preguntas dinamicas.
- Requisitos de login.
- Captchas.
- Duplicados entre portales.
- Aplicaciones accidentales si no se disena bien la autorizacion.
- Exposicion de datos sensibles si se integra IA sin filtros.
- El contrato JSON necesita versionado antes de implementar aplicaciones reales.
- Google Sheets puede divergir del estado local si no hay estrategia clara de sincronizacion.

## Principios de diseno recomendados

- Local-first: todo debe funcionar localmente sin depender de Google Sheets o IA.
- Human-in-the-loop: login, captcha, decisiones finales y envio deben poder pasar por el usuario.
- Explicit approval: aplicar solo si `autorizar_aplicacion=si`.
- Portal isolation: cada portal debe tener su propio modulo.
- Fail controlled: si algo falla, registrar estado, motivo y accion recomendada.
- No wasted generation: no generar cartas para descartadas.
- Retry-friendly: no marcar como ignoradas permanentes las filas que requieren intervencion.
- Auditability: toda accion debe dejar evidencia local.
- Expandable but simple: evitar sobrearquitectura temprana.

## Archivos que conviene adjuntar a la IA

Adjuntar:

- `README.md`
- `FASE2.md`
- `CONTEXTO_IA.md`
- `profile.example.json`

Opcional si se quiere entrar a codigo:

- `botjobs/app.py`
- `botjobs/search.py`
- `botjobs/workbook.py`
- `botjobs/ranking.py`
- `botjobs/schema.py`
- `botjobs/extractors.py`
- `botjobs/browser.py`

No adjuntar salvo necesidad:

- CV real.
- `READMElocal.md`, porque contiene rutas personales.
- `cache/`.
- `output/`, salvo que se quiera analizar un ejemplo de resultado.

## Estado final resumido

BotJobs ya es util como herramienta local de compendio y filtrado. La siguiente decision de arquitectura importante es como implementar Fase 2 sin perder control humano, sin aplicar accidentalmente y sin acoplar demasiado el sistema a cambios de portales. La planeacion debe enfocarse en estados, contrato de datos, aplicadores por portal, evidencia de acciones, seguridad local e integraciones futuras con IA y Google Sheets.
