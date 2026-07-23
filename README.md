# BotJobs

Herramienta local personal para buscar vacantes tech Junior, entrar a portales laborales, extraer descripciones, filtrar oportunidades y generar materiales de aplicacion.

La API local para ejecutar acciones controladas se documenta en [BACKEND.md](BACKEND.md), la app React Native en [MOBILE.md](MOBILE.md) y el plan de automatizacion de aplicaciones en [FASE2.md](FASE2.md).

## Objetivo principal

BotJobs debe evitar perder tiempo aplicando a ofertas laborales irrelevantes. Para eso, el flujo central debe funcionar de forma automatizada:

- Buscar vacantes automaticamente en Indeed, LinkedIn, OCC, Computrabajo y Glassdoor.
- Entrar a los portales laborales para consultar los resultados.
- Extraer descripciones, empresa, ubicacion, modalidad, salario, fecha, link y correo de contacto cuando exista.
- Filtrar ofertas recientes, idealmente no mayores a 2 semanas.
- Rankear vacantes segun el perfil y criterios laborales definidos.
- Generar resultados estructurados en `.json` para la app y cartas personalizadas en `.md` solo para vacantes preseleccionadas.

Si un portal presenta login, captcha, verificacion humana o bloqueo normal de plataforma, el bot debe detenerse, avisar al usuario y continuar despues de la intervencion manual.

## Fase actual

Fase actual: compendio local operativo. El sistema ya busca, extrae, rankea, registra intervenciones y genera cartas solo para vacantes preseleccionadas. No aplica a vacantes ni envia correos.

La automatizacion de aplicaciones se documenta aparte en [FASE2.md](FASE2.md).

Entrada:

- Busqueda automatica en Indeed, LinkedIn, OCC, Computrabajo y Glassdoor.
- Extraccion automatica desde links de vacantes.
- `vacantes.template.xlsx`: respaldo manual para pegar links/vacantes y validar ranking, cartas e investigacion cuando un portal bloquee o cambie su estructura.
- `profile.example.json`: perfil base de Rene Alexis Segura Perez, filtros laborales y criterios de ranking.

Salida:

- `output/botjobs_resultados.json`
  - `resumen_ejecucion`
  - `vacantes_detectadas`
  - `preseleccionadas`
  - `descartadas`
  - `aplicadas`
  - `requiere_intervencion`
  - `empresas_investigadas`
- `output/cartas/*.md`: carta personalizada por vacante.

## Estado operativo actual

Implementado:

- CLI local con `--auto-search`, `--extract-links`, `--browser`, `--research`, `--refresh-cache`, `--portals` y `--max-results`.
- Busqueda automatica inicial en Indeed, LinkedIn, OCC, Computrabajo y Glassdoor.
- Seleccion declarativa de portales con `--portals indeed,linkedin,occ,computrabajo,glassdoor`.
- Extraccion desde links pegados manualmente en `.xlsx`.
- Extraccion con HTML directo y modo navegador automatizado para paginas que requieren renderizado.
- Deteccion controlada de `captcha`, `login_requerido`, `bloqueado`, `navegador_bloqueado`, `estructura_no_reconocida`, `sin_descripcion` y `error_red`.
- Cache local de HTML bruto con TTL de 120 horas.
- Memoria local de vacantes descartadas mediante `cache/ignored_urls.json`.
- JSON con resumen, vacantes detectadas, preseleccionadas, descartadas, aplicadas, intervenciones y empresas investigadas.
- Cartas `.md` y mensajes cortos solo para vacantes `preseleccionada`.
- Decision manual por vacante, CV activo por identificador y preparacion asistida de aplicaciones aprobadas.
- Pantalla movil de Documentos y selección de CV por vacante.
- Seguimiento de aplicaciones, evidencia visual, métricas e historial persistente.
- Confirmación explícita en la app antes de solicitar envíos.
- `--apply-approved --dry-run` valida autorizacion, CV y carta; `--browser` prepara campos compatibles, detecta barreras, guarda captura y registra el seguimiento.
- `--login-portal PORTAL` abre un perfil persistente para resolver login o captcha manualmente.
- `--retry-intervention` reintenta solo aplicaciones detenidas.
- `--submit --confirm-submit ENVIAR` habilita envio controlado; bloquea dominios desconocidos y vacantes ya enviadas o con envio incierto.
- Ranking por industria, salario, horario, remoto, ubicacion, seniority y skills.
- Filtros para no generar cartas de vacantes descartadas.

Limitaciones actuales:

- LinkedIn está fuera del selector de la app móvil por bloqueo de Cloudflare (`requiere_intervencion`); se retomará después del MVP.
- El sistema no resuelve captchas, logins ni verificaciones humanas.
- Algunos portales bloquean busquedas o detalles; esos casos quedan en `requiere_intervencion`.
- La investigacion de empresa es basica y no usa IA.
- Las cartas usan plantillas simples, no redaccion inteligente con modelo de lenguaje.
- No existe sincronizacion directa con Google Sheets.
- No envia formularios ni correos: `--submit` falla de forma segura hasta que exista un adaptador verificado por portal.

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

Para buscar solo en Indeed y OCC:

```powershell
python .\bot_jobs.py --auto-search --profile .\profile.example.json --out .\output --portals indeed,occ --max-results 10
```

`--portals` es la forma declarativa de indicar en que plataformas debe buscar el bot. Si no se declara, intenta buscar en todos los portales soportados.

Para forzar descarga nueva e ignorar el cache HTML:

```powershell
python .\bot_jobs.py --auto-search --profile .\profile.example.json --out .\output --portals indeed,occ --max-results 10 --refresh-cache
```

Estado actual: `--auto-search` usa paginas de resultados publicas y extrae links candidatos. Si un portal bloquea, cambia su estructura o no muestra resultados publicos, puede devolver pocos resultados o ninguno. Los links encontrados pasan por los extractores del paso 5.

## Roadmap del nucleo

1. Normalizar el contrato de datos de vacantes para que Excel, links y portales usen la misma estructura interna.
2. Separar el script en modulos: perfil, ranking, workbook, cartas, investigacion y portales.
3. Crear modo `--extract-links` para abrir links pegados en el `.xlsx` y extraer datos de cada vacante. Estado: implementado con extractor generico.
4. Agregar navegador automatizado para abrir paginas reales y detectar captcha, login o bloqueo. Estado: implementado como `--extract-links --browser`.
5. Implementar extractores por portal, uno por uno: Indeed, Computrabajo, OCC, Glassdoor y LinkedIn. Estado: implementacion inicial completa para links de vacantes.
6. Crear modo `--auto-search` para buscar vacantes automaticamente en los portales soportados. Estado: implementado en version inicial.
7. Agregar cache local de HTML/texto extraido para evitar repetir navegacion innecesaria. Estado: implementado con HTML bruto, TTL de 120 horas y `--refresh-cache`.
8. Registrar estados de extraccion: `ok`, `captcha`, `login_requerido`, `bloqueado`, `estructura_no_reconocida`, `sin_descripcion` y `error_red`. Estado: implementado con `cache_hit`, `motivo_intervencion`, `accion_recomendada` y hoja `requiere_intervencion`.
9. Mejorar ranking con datos reales: industria, seniority, salario, modalidad, spam y trabajos por proyecto. Estado: implementado con inferencias desde titulo/descripcion.
10. Generar resultado operativo con secciones de detectadas, preseleccionadas, descartadas, requiere intervencion, empresas investigadas y aplicadas. Estado: implementado en JSON para backend y app movil.
11. Agregar reporte de ejecucion con conteos de detectadas, extraidas, preseleccionadas, descartadas, intervenciones y cartas. Estado: implementado en salida CLI.
12. Probar primero con Indeed en una busqueda pequena de maximo 10 resultados.
13. Expandir portal por portal sin agregar uno nuevo hasta que el anterior extraiga y falle de forma controlada. Estado: completada la primera ronda de validacion para Indeed, OCC, Computrabajo, Glassdoor y LinkedIn.
14. Mantener README actualizado con estado real de soporte por portal y comandos disponibles. Estado: implementado como seccion de estado operativo, soporte por portal e integraciones futuras.

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
- `ignorar_en_futuro`
- `cache_hit`
- `motivo_intervencion`
- `accion_recomendada`
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
- `botjobs/workbook.py`: lectura de la plantilla manual `.xlsx`.
- `botjobs/results.py`: escritura directa de resultados `.json`.
- `botjobs/letters.py`: cartas y mensajes cortos para reclutadores.
- `botjobs/research.py`: investigacion web de empresas.
- `botjobs/search.py`: busqueda automatica de links candidatos en portales.
- `botjobs/cache.py`: cache HTML bruto y memoria local de URLs descartadas.
- `botjobs/extractors.py`: extraccion generica de datos desde links.
- `botjobs/browser.py`: extraccion con navegador automatizado.
- `botjobs/browser_extract.mjs`: script Playwright usado por el extractor de navegador.
- `botjobs/extractor_utils.py`: utilidades compartidas para extractores HTML.
- `botjobs/portals/`: extractores especificos por portal.
- `botjobs/utils.py`: utilidades compartidas.

## Soporte por portal

- Indeed: extractor inicial para links de vacantes; puede encontrar candidatos, pero algunas paginas de detalle bloquean y quedan en intervencion.
- Computrabajo: extractor inicial para links de vacantes; la busqueda publica puede bloquear y queda registrada como intervencion.
- OCC: extractor inicial para links de vacantes; la busqueda publica puede responder HTTP 403 y queda registrada como intervencion.
- Glassdoor: extractor inicial para links de vacantes; filtra `job-listing` y `partner/jobListing` para evitar paginas de navegacion.
- LinkedIn: extractor inicial para links de vacantes; filtra `/jobs/view` para evitar links internos de busqueda.

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
- Las vacantes descartadas se marcan con `ignorar_en_futuro=si` y sus URLs se guardan localmente para saltarlas en siguientes corridas.
- Las busquedas bloqueadas por portal o filas que requieren intervencion manual no se marcan como `ignorar_en_futuro`, aunque queden descartadas por filtros. Deben poder reintentarse con `--browser` o revisarse manualmente.
- El ranking infiere industria, modalidad, seniority, salario y horas desde titulo/descripcion cuando el portal no entrega esos campos.

## Cache local

- Carpeta: `cache/`
- Contenido: HTML bruto y `ignored_urls.json`
- TTL por defecto: 120 horas
- Git: `cache/` esta ignorado

El cache reduce llamadas repetidas a portales. Si necesitas volver a descargar todo, usa `--refresh-cache`.

## Estado real por portal en auto-search

- Indeed: encuentra links candidatos, pero algunas paginas de detalle pueden bloquear y quedar en `requiere_intervencion`.
- OCC: la busqueda publica puede responder con bloqueo HTTP 403. El bot genera filas de intervencion con `estado_extraccion=bloqueado`, `requiere_intervencion=si` e `ignorar_en_futuro=no`.
- Computrabajo: la busqueda publica puede responder con bloqueo. El bot lo registra como intervencion y no lo agrega a ignoradas permanentes.
- Glassdoor: extrae ofertas reales desde `job-listing` y `partner/jobListing`; el filtro evita links de navegacion como paginas de busqueda o menus.
- LinkedIn: extrae ofertas reales desde `/jobs/view`; el filtro evita links internos de busqueda como `#main-content`.

Cuando un portal bloquea la busqueda, el comportamiento correcto es registrar la fila como intervencion, no guardarla como descartada permanente.

## Futuras implementaciones

Integraciones de portales:

- Mejorar busqueda especifica por portal cuando cambien estructuras publicas.
- Soportar sesiones manuales persistentes para portales que requieren login, sin automatizar evasion de captchas.
- Agregar reintentos guiados para filas `requiere_intervencion` despues de que el usuario resuelva login/captcha.
- Mejorar deduplicacion entre URLs equivalentes de la misma vacante.

Automatizacion de aplicacion:

- Ver plan detallado en [FASE2.md](FASE2.md).
- La app ya permite guardar decision manual por vacante: aprobada, descartada o revision.
- Preparacion asistida implementada para vacantes aprobadas: detecta el boton de aplicacion, carga CV, pega carta y guarda evidencia cuando el formulario lo permite.
- Seguimiento JSON implementado en `aplicaciones`: autorizada, preparada u omitida y su motivo.
- Adaptadores iniciales implementados para LinkedIn, Indeed, OCC, Computrabajo y Glassdoor; requieren validacion operativa con cuentas y vacantes reales antes de considerarse estables.
- Pendiente: seleccionar un CV distinto por vacante; actualmente se usa el CV activo.
- Enviar emails a reclutadores solo cuando exista correo de contacto y el usuario lo autorice.

IA y materiales:

- Usar IA para redactar cartas mas inteligentes; por ahora usa plantillas simples.
- Investigar empresa con resumen mas profundo antes de redactar.
- Generar variantes de carta por industria, seniority, idioma y stack tecnico.
- Sugerir si una vacante necesita un CV alternativo.

Google Sheets y validacion visual:

- Actualizar Google Sheets directamente.
- Sincronizar resultados JSON con Google Sheets.
- Generar un resumen ejecutivo de corrida dentro de Google Sheets.

Calidad y aprendizaje:

- Aprender de vacantes falsas, spam o descartes recurrentes.
- Crear reglas configurables para empresas, industrias o patrones bloqueados.
- Generar metricas historicas por portal: ofertas utiles, bloqueos, descartes y preseleccionadas.
- Agregar mas pruebas automatizadas para ranking, extractores y resultados.
