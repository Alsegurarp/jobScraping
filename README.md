# BotJobs CLI

Herramienta local para buscar, extraer, filtrar y rankear vacantes tech, generar cartas y preparar postulaciones asistidas. El producto se ejecuta exclusivamente desde una terminal en la maquina fisica del usuario.

No incluye aplicacion movil, API web ni despliegue remoto.

Version de entrega: **1.0.0**.

## Estado

El nucleo permite:

- buscar en Indeed, LinkedIn, OCC, Computrabajo y Glassdoor;
- leer vacantes desde `vacantes.template.xlsx`;
- extraer datos con HTTP o navegador automatizado;
- detectar login, captcha, bloqueo y cambios de estructura;
- rankear contra `profile.example.json`;
- guardar resultados en `output/botjobs_resultados.json`;
- generar cartas Markdown para vacantes preseleccionadas;
- preparar postulaciones aprobadas y conservar evidencia local;
- mantener cache, decisiones, documentos y sesiones en el equipo local.

El sistema no evade captchas ni verificaciones humanas. El envio final permanece bloqueado salvo confirmacion explicita.

## Instalacion

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 -IncludeDev
powershell -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

El instalador crea `.venv` y utiliza las versiones fijas de `requirements.lock.txt`. Omite `-IncludeDev` en una instalación que no ejecutará pruebas.

## Comprobacion rapida

```powershell
python .\bot_jobs.py --help
python .\bot_jobs.py doctor
python -m pytest -q
python .\bot_jobs.py --demo
```

`doctor` comprueba la version de Python, el perfil, la plantilla, la escritura en el directorio de salida y la disponibilidad del runtime de navegador. Para diagnosticar una busqueda que no usa plantilla:

```powershell
python .\bot_jobs.py doctor --auto-search
```

Para exigir tambien el runtime de navegador:

```powershell
python .\bot_jobs.py doctor --auto-search --browser
```

Los estados `ERROR` producen codigo de salida `1`; una `ADVERTENCIA` sobre el navegador opcional no bloquea los modos HTTP.

## Proceso completo esperado

El flujo normal del proyecto se ejecuta en este orden:

1. Instalar y verificar el entorno.
2. Configurar el perfil laboral.
3. Agregar y activar al menos un CV.
4. Buscar vacantes automáticamente o cargarlas en la plantilla.
5. Revisar el ranking, descartes, intervenciones y cartas generadas.
6. Registrar una decisión por cada vacante revisada.
7. Ejecutar una simulación con `--dry-run`.
8. Preparar las aplicaciones autorizadas con navegador, sin enviar.
9. Resolver manualmente login o captcha y revisar la evidencia.
10. Opcionalmente habilitar el envío con confirmación literal.
11. Crear un respaldo de resultados y estado local.

### Inputs necesarios

| Input | Obligatorio | Formato o valores | Uso |
|---|---|---|---|
| Perfil | Sí | JSON | Identidad, filtros, skills y preferencias de ranking. |
| CV | Sí para preparar o enviar | PDF válido, máximo 4 MB | Documento cargado en formularios. |
| Vacantes | Sí | Búsqueda automática o `vacantes.template.xlsx` | Fuente de URLs y datos laborales. |
| Decisión | Sí para postular | `aprobada`, `descartada` o `revision` | Autorización explícita por URL. |
| Carta | Sí para preparar o enviar | `.md` generado para una preseleccionada | Texto personalizado de postulación. |
| Navegador | Solo para extracción o postulación asistida | Node y Chrome o Edge | Renderizado, sesión, formularios y evidencia. |
| Confirmación de envío | Solo para enviar | Texto literal `ENVIAR` | Autoriza el clic final. |

El perfil predeterminado es `profile.example.json`. Para uso personal se recomienda crear una copia, por ejemplo `profile.local.json`, y pasarla con `--profile`. Sus campos operativos principales son:

- `name`, `email`, `headline` y `summary`;
- `minimum_salary_mxn` y `minimum_unpublished_salary_mxn`;
- `max_hours_per_week` y `max_post_age_days`;
- `minimum_skill_matches`;
- `skills` y `target_roles`;
- `allowed_industries` y `blocked_industries`;
- `preferred_locations` e `interest_keywords`.

No es necesario incluir una ruta de CV en el perfil: el CV operativo se administra con el comando `cv` y se guarda bajo `runtime/`.

### Output esperado por etapa

| Etapa | Output esperado |
|---|---|
| `doctor` | Una línea `OK`, `ADVERTENCIA` o `ERROR` por dependencia. |
| `cv add` | JSON con `cv_id`, nombre, tamaño, estado activo y fecha. |
| Búsqueda o extracción | `output/botjobs_resultados.json`. |
| Ranking | Tablas JSON de detectadas, preseleccionadas, descartadas e intervenciones. |
| Cartas | Archivos `output/cartas/*.md` para preseleccionadas. |
| `decisions set` | JSON con URL, decisión, nota, CV asociado y fecha. |
| `--dry-run` | Lista de aplicaciones autorizadas u omitidas; ningún archivo cambia. |
| Preparación | Historial `aplicaciones`, captura bajo `runtime/evidence/` y URL final. |
| Envío | Registro `en_progreso`, `confirmado` o `incierto` en `runtime/submitted_applications.json`. |
| Respaldo | ZIP con `runtime/`, `cache/` y `output/`. |

## Decisiones y CV locales

### Subir un CV paso a paso

1. Coloca el PDF en una ruta legible desde la terminal. La ruta puede contener espacios; en ese caso debe ir entre comillas.
2. Comprueba que la extensión sea `.pdf`, que el archivo comience con una firma PDF válida y que pese como máximo 4 MB.
3. Ejecuta:

```powershell
python .\bot_jobs.py cv add --file "C:\ruta\Rene Alexis CV.pdf"
```

Output esperado:

```json
{
  "cv_id": "IDENTIFICADOR_DE_16_CARACTERES",
  "filename": "Rene Alexis CV.pdf",
  "size_bytes": 123456,
  "active": true,
  "added_at": "2026-08-11T22:00:00"
}
```

`cv_id` se deriva del contenido, por lo que volver a agregar el mismo PDF no crea un duplicado. El primer CV queda activo automáticamente y el archivo se copia a:

```text
runtime/documents/cv/IDENTIFICADOR.pdf
runtime/documents/cv/IDENTIFICADOR.json
```

4. Verifica los CV registrados:

```powershell
python .\bot_jobs.py cv list
```

5. Si existen varios, activa el que se enviará:

```powershell
python .\bot_jobs.py cv activate --cv-id IDENTIFICADOR
```

Solo un CV puede estar activo. También es posible asociar explícitamente un `cv_id` distinto a una decisión concreta.

6. Para reemplazar el CV, agrega el PDF nuevo, actívalo y conserva el anterior hasta verificar el cambio. Después puede eliminarse con:

```powershell
python .\bot_jobs.py cv remove --cv-id IDENTIFICADOR_ANTERIOR --confirm BORRAR
```

Si se elimina el CV activo y existe otro, BotJobs activa automáticamente uno de los restantes.

### Revisar vacantes y registrar decisiones

Registrar y consultar una decisión por URL:

```powershell
python .\bot_jobs.py decisions set --url "https://portal.example/vacante" --decision aprobada --cv-id IDENTIFICADOR --note "Revisada"
python .\bot_jobs.py decisions list
```

Valores permitidos: `aprobada`, `descartada` y `revision`.

Las eliminaciones requieren confirmación literal para evitar pérdidas accidentales:

```powershell
python .\bot_jobs.py decisions remove --url "https://portal.example/vacante" --confirm BORRAR
python .\bot_jobs.py cv remove --cv-id IDENTIFICADOR --confirm BORRAR
```

Los CV se validan por extensión, firma PDF y tamaño máximo de 4 MB. Se copian a `runtime/documents/cv/`; no se conserva una referencia a la ruta de origen.

## Flujos principales

Busqueda automatica:

```powershell
python .\bot_jobs.py --auto-search --profile .\profile.example.json --out .\output --portals indeed,occ --max-results 10
```

Inputs:

- `--profile`: archivo de perfil;
- `--portals`: uno o varios entre `indeed`, `linkedin`, `occ`, `computrabajo` y `glassdoor`;
- `--max-results`: máximo total de candidatos; debe utilizarse un entero positivo y pequeño por portal;
- `--out`: directorio de resultados;
- `--browser`: opcional para páginas renderizadas;
- `--research`: opcional para investigación web;
- `--refresh-cache`: opcional para ignorar HTML vigente.

Procesamiento de la plantilla local:

```powershell
python .\bot_jobs.py --profile .\profile.example.json --jobs .\vacantes.template.xlsx --out .\output --extract-links
```

La hoja `vacantes` acepta estos campos canónicos:

```text
titulo, empresa, portal, url, descripcion, ubicacion, modalidad,
salario, fecha_publicacion, email_contacto, industria_detectada,
fuente_extraccion, requiere_intervencion, estado_extraccion,
ignorar_en_futuro, cache_hit, motivo_intervencion,
accion_recomendada, horas_semana, seniority, idioma, url_empresa
```

Para una entrada manual mínima basta proporcionar la URL; título, empresa y descripción mejoran el resultado si el portal bloquea la extracción.

Extraccion con navegador:

```powershell
python .\bot_jobs.py --profile .\profile.example.json --jobs .\vacantes.template.xlsx --out .\output --extract-links --browser
```

Abrir una sesion persistente para intervencion manual:

```powershell
python .\bot_jobs.py --login-portal indeed
```

Validar postulaciones autorizadas sin modificar resultados:

```powershell
python .\bot_jobs.py --apply-approved --jobs .\output\botjobs_resultados.json --dry-run
```

Antes de este comando deben existir:

- una fila preseleccionada en el JSON;
- una decisión `aprobada` para la misma URL;
- un CV activo o asociado a esa decisión;
- el `carta_id` y su archivo correspondiente en `output/cartas/`;
- un dominio perteneciente a un portal soportado.

Aunque se combine con `--browser`, `--dry-run` nunca abre el navegador ni modifica resultados, evidencia o estado local.

Preparar formularios autorizados sin enviar:

```powershell
python .\bot_jobs.py --apply-approved --jobs .\output\botjobs_resultados.json --out .\output --runtime .\runtime --browser
```

Los intentos conservan `estado_aplicacion`, resultado, captura y URL final en los archivos locales. Para reintentar exclusivamente los casos detenidos por intervención:

```powershell
python .\bot_jobs.py --apply-approved --jobs .\output\botjobs_resultados.json --out .\output --runtime .\runtime --browser --retry-intervention
```

El envío controlado está habilitado explícitamente para adaptadores de Indeed, LinkedIn, OCC, Computrabajo y Glassdoor. Requiere confirmación literal:

```powershell
python .\bot_jobs.py --apply-approved --jobs .\output\botjobs_resultados.json --out .\output --runtime .\runtime --browser --submit --confirm-submit ENVIAR
```

Antes de abrir el navegador se registra `en_progreso`. Después del intento queda `confirmado` o `incierto`; ambos estados bloquean repeticiones. Una redirección fuera del dominio permitido detiene el envío. Si el programa se cierra durante el intento, se debe revisar manualmente el portal: BotJobs bloqueará el reintento porque no puede asegurar que el envío no ocurrió.

### Estados esperados

- `preseleccionada`: cumple los filtros y tiene carta.
- `descartada`: incumple una o más reglas; consultar `flags` y `razon_menos_250`.
- `requiere_intervencion`: necesita login, captcha, revisión humana o adaptación técnica.
- `autorizada`: aprobada y con materiales válidos durante simulación.
- `omitida`: falta autorización, CV, carta, portal compatible o ya existe un envío.
- `preparada`: formulario completado sin clic final.
- `aplicada`: el portal mostró confirmación reconocida.
- `fallida`: error ocurrido antes de poder confirmar un intento.
- `en_progreso`: reserva escrita justo antes del intento de envío.
- `confirmado`: envío confirmado; nunca se repite automáticamente.
- `incierto`: pudo haberse enviado; nunca se repite automáticamente y exige revisión manual.

### Comprobación final esperada

Una operación normal debe terminar con código `0` y mostrar un reporte similar a:

```text
Listo: output\botjobs_resultados.json
Reporte:
- Detectadas: 10
- Extraidas correctamente: 7
- Preseleccionadas: 3
- Descartadas: 7
- Requieren intervencion: 2
- Cartas generadas: 3
- Cache hits: 0
- Ignoradas en futuro: 5
```

Los números varían según los portales y el perfil. Un portal bloqueado no implica corrupción: debe aparecer como intervención con una acción recomendada y no debe marcarse para ignorar permanentemente.

## Datos locales

- `profile.example.json`: perfil y reglas de ranking.
- `vacantes.template.xlsx`: entrada manual opcional.
- `output/`: resultados y cartas.
- `cache/`: HTML y URLs ignoradas.
- `runtime/`: decisiones, CV, evidencia, sesiones y registro de envios.

`output/`, `cache/` y `runtime/` no se versionan.

## Respaldo y restauracion

```powershell
python .\bot_jobs.py backup create --project . --file .\backups\botjobs.zip
python .\bot_jobs.py backup restore --project . --file .\backups\botjobs.zip --confirm RESTAURAR
```

El respaldo incluye `runtime/`, `cache/` y `output/`. Se escribe de forma atómica y la restauración rechaza rutas que intenten salir del proyecto. Consulta [docs/MANUAL_OPERATIVO.md](docs/MANUAL_OPERATIVO.md) y [docs/CHECKLIST_ENTREGA.md](docs/CHECKLIST_ENTREGA.md) antes de mover la instalación a otra máquina.

## Estructura

- `bot_jobs.py`: punto de entrada.
- `botjobs/app.py`: argumentos y orquestacion.
- `botjobs/search.py`: descubrimiento de vacantes.
- `botjobs/extractors.py`: extraccion de datos.
- `botjobs/portals/`: adaptadores por portal.
- `botjobs/ranking.py`: reglas y puntuacion.
- `botjobs/results.py`: salida JSON.
- `botjobs/letters.py`: cartas y mensajes.
- `botjobs/apply.py`: preparacion y envio controlado.
- `tests/`: pruebas automatizadas del producto CLI.
- `docs/BITACORA_SPRINTS.md`: plan de entrega y evidencia TDD.

## Entrega

Los sprints, criterios de aceptacion, evidencias y riesgos se administran en [docs/BITACORA_SPRINTS.md](docs/BITACORA_SPRINTS.md). Ningun entregable se considera terminado sin pruebas automatizadas en verde y una comprobacion reproducible desde PowerShell.
