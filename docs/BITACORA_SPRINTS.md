# Bitacora de sprints de entrega

## Proposito

Esta es la fuente oficial para conducir la entrega de BotJobs como CLI local. Cada incremento debe poder instalarse, probarse y ejecutarse desde PowerShell en la maquina fisica del usuario, sin aplicacion movil, API web, contenedores ni servicios remotos.

## Politica TDD obligatoria

Todo entregable sigue este ciclo:

1. **Rojo:** escribir una prueba que describa el comportamiento y comprobar que falla por la razon esperada.
2. **Verde:** implementar el cambio minimo que haga pasar la prueba.
3. **Refactor:** simplificar sin modificar comportamiento y ejecutar toda la suite.
4. **Aceptacion:** ejecutar el comando real del criterio de aceptacion en PowerShell.
5. **Evidencia:** registrar fecha, commit, pruebas, resultado y observaciones en la tabla de bitacora.

No se acepta como terminado un entregable con pruebas omitidas, pruebas no deterministas, fallos conocidos sin registrar o pasos manuales no documentados.

## Definition of Ready

- Comportamiento y limites definidos.
- Criterios de aceptacion observables.
- Fixtures locales disponibles y sin secretos.
- Riesgos de red, navegador y escritura identificados.
- Prueba roja propuesta antes de implementar.

## Definition of Done

- Pruebas unitarias del incremento en verde.
- Suite completa en verde con `python -m pytest -q`.
- Ayuda del CLI coherente con `python .\bot_jobs.py --help`.
- Errores devuelven mensaje accionable y codigo de salida distinto de cero.
- Ningun secreto ni ruta personal queda versionado.
- README y esta bitacora reflejan el comportamiento real.
- Evidencia de aceptacion registrada.

## Sprint 0 - Rebase a CLI local

**Objetivo:** eliminar la arquitectura movil/servidor y establecer una linea base reproducible.

**Estado:** aceptado el 2026-08-11.

Entregables:

- Retirar Expo, React Native, FastAPI, Vercel, Docker y sus pruebas exclusivas.
- Reducir dependencias al producto CLI.
- Consolidar documentacion y alcance local.
- Mantener en verde las pruebas del nucleo.

Pruebas primero:

- Prueba de humo de `--help` con salida exitosa.
- Prueba que importe todos los modulos del paquete `botjobs`.
- Prueba de demo aislada en un directorio temporal.

Criterios de aceptacion:

```powershell
python -m pytest -q
python .\bot_jobs.py --help
python .\bot_jobs.py --demo
```

## Sprint 1 - Configuracion y diagnostico local

**Objetivo:** garantizar que una instalacion nueva detecte faltantes antes de una corrida real.

**Estado:** aceptado el 2026-08-11.

Entregables:

- Comando `doctor` que valide Python, perfil, plantilla, directorios y navegador opcional.
- Mensajes accionables sin trazas para errores esperados.
- Creacion segura de directorios locales.
- Guia de instalacion reproducible.

Pruebas primero:

- Perfil inexistente o JSON invalido.
- Plantilla inexistente cuando el modo la requiere.
- Directorio de salida no escribible.
- Navegador ausente en modo HTTP y en modo navegador.
- Salida y codigos de retorno de `doctor`.

Criterio de aceptacion: `python .\bot_jobs.py doctor` informa `OK`, advertencia o error por cada dependencia.

## Sprint 2 - Busqueda y extraccion deterministas

**Objetivo:** estabilizar el descubrimiento y la normalizacion de vacantes sin depender de pruebas contra portales vivos.

**Estado:** aceptado el 2026-08-11.

Entregables:

- Fixtures HTML anonimizadas por portal.
- Contrato unico de vacante validado antes del ranking.
- Deduplicacion canonica de URLs.
- Estados controlados para red, login, captcha, bloqueo y estructura desconocida.

Pruebas primero:

- Un caso valido y cada caso de error por portal.
- URLs equivalentes con parametros de rastreo.
- Campos ausentes y JSON-LD malformado.
- Cache vigente, vencido y forzado con `--refresh-cache`.

Criterio de aceptacion: la suite de extractores funciona sin internet; una prueba manual limitada usa `--max-results 5`.

## Sprint 3 - Ranking y resultados auditables

**Objetivo:** hacer explicable y estable cada preseleccion o descarte.

**Estado:** aceptado el 2026-08-11.

Entregables:

- Reglas de ranking cubiertas por tablas de casos.
- Motivos de descarte y habilidades coincidentes trazables.
- Esquema versionado del JSON de salida.
- Escritura atomica para no corromper resultados previos.

Pruebas primero:

- Limites de salario, antiguedad, jornada, modalidad, ubicacion y seniority.
- Industrias permitidas y bloqueadas.
- Orden estable cuando existen empates.
- Falla durante escritura conservando el archivo anterior.

Criterio de aceptacion: dos ejecuciones con las mismas entradas producen las mismas decisiones, salvo marcas de tiempo documentadas.

## Sprint 4 - Decisiones y CV desde CLI

**Objetivo:** reemplazar completamente la administracion que antes dependia de una interfaz.

**Estado:** aceptado el 2026-08-11.

Entregables:

- `decisions list|set|remove` por URL.
- `cv list|add|activate|remove` con validacion PDF.
- Identificadores estables y almacenamiento bajo `runtime/`.
- Confirmacion para operaciones destructivas.

Pruebas primero:

- Decision valida, invalida, reemplazada y eliminada.
- PDF valido, extension falsa, archivo excedido y CV inexistente.
- Activacion exclusiva de un CV.
- Operaciones sobre rutas fuera del espacio permitido.

Criterio de aceptacion: una vacante puede aprobarse y asociarse a un CV usando solo PowerShell.

## Sprint 5 - Preparacion segura de postulaciones

**Objetivo:** preparar formularios autorizados sin realizar envios accidentales.

**Estado:** aceptado el 2026-08-11.

Entregables:

- `--dry-run` completamente libre de efectos secundarios.
- Validacion previa de decision, CV, carta, portal y envio anterior.
- Perfiles persistentes por portal.
- Evidencia y resultado local por intento.

Pruebas primero:

- Solo se procesan decisiones aprobadas.
- Material faltante genera `omitida`.
- Login/captcha genera `requiere_intervencion`.
- Preparacion no pulsa el control final de envio.
- Reintento procesa exclusivamente intervenciones.

Criterio de aceptacion: una vacante de prueba llega a `preparada` y conserva captura, URL final y registro local.

## Sprint 6 - Envio controlado e idempotencia

**Objetivo:** permitir el envio solo en adaptadores verificados y con confirmacion inequívoca.

**Estado:** aceptado el 2026-08-11.

Entregables:

- Lista explicita de adaptadores habilitados para envio.
- Confirmacion literal `ENVIAR`.
- Registro previo de intento y posterior de resultado.
- Bloqueo de reenvio confirmado o incierto.
- Recuperacion segura tras cierre inesperado.

Pruebas primero:

- Falta de `--browser` o confirmacion.
- Dominio no soportado y redireccion a otro dominio.
- Doble ejecucion del mismo envio.
- Excepcion antes y despues del clic final.
- Evidencia de confirmacion del portal.

Criterio de aceptacion: una segunda ejecucion nunca repite un intento cuyo resultado pueda haber sido enviado.

## Sprint 7 - Empaque y entrega fisica

**Objetivo:** producir una entrega instalable, operable y recuperable en la maquina destino.

**Estado:** aceptado el 2026-08-11.

Entregables:

- Script de instalacion y verificacion para PowerShell.
- Version fija y reporte de dependencias.
- Copia de seguridad y restauracion de `runtime/`, `cache/` y `output/`.
- Manual operativo, solucion de problemas y checklist de entrega.
- Corrida de aceptacion completa con datos anonimizados.

Pruebas primero:

- Instalacion en entorno virtual limpio.
- Rutas con espacios y caracteres no ASCII.
- Restauracion desde respaldo.
- Interrupcion de una corrida y ejecucion posterior.
- Suite offline seguida de prueba controlada con red.

Criterio de aceptacion: una persona puede instalar, verificar, ejecutar y recuperar BotJobs siguiendo exclusivamente el README.

## Bitacora de evidencia

Agregar una fila al cerrar cada entregable. El estado permitido es `pendiente`, `en curso`, `bloqueado` o `aceptado`.

| Fecha | Sprint | Entregable | Estado | Prueba roja | Suite verde | Aceptacion | Commit | Observaciones |
|---|---:|---|---|---|---|---|---|---|
| 2026-08-11 | 0 | Retiro de implementacion movil/servidor | aceptado | N/A, cambio de alcance | `6 passed` | `--help` y `--demo` exitosos | Pendiente | Se conserva exclusivamente el nucleo CLI. |
| 2026-08-11 | 0 | Pruebas de humo del CLI | aceptado | Demo aislada fallo al no encontrar `profile.example.json` | `9 passed` | `--help` y `--demo` exitosos | Pendiente | Se agregaron pruebas de ayuda, importacion completa y demo aislada; el demo ya no depende del directorio actual para localizar el perfil. |
| 2026-08-11 | 1 | Comando `doctor` y errores operativos | aceptado | Modulo ausente; luego fallos con traceback y Python sin validacion | `19 passed` | `doctor` manual y `doctor --auto-search --browser` exitosos | Pendiente | Valida Python 3.10+, perfil, plantilla, salida y Node; los errores esperados ya son concisos. |
| 2026-08-11 | 1 | Regresion de sprints 0 y 1 | aceptado | N/A, ejecucion de comprobacion | `19 passed` | `doctor` y `--demo` exitosos | Pendiente | Evidencia en `docs/tests/2026-08-11-sprints-0-1.md`. |
| 2026-08-11 | 2 | Extraccion determinista y contrato | aceptado | Faltaban validador y canonicalizacion; JSON-LD roto figuraba `ok` | `49 passed` | Fixtures de cinco portales en verde | Pendiente | Contrato validado antes del ranking, barreras controladas y URLs sin rastreo. |
| 2026-08-11 | 2 | Aceptacion limitada de Indeed | aceptado | Errores de busqueda se reabrian y quedaban ignorables | `50 passed` | 5 errores de red controlados, 0 ignorados | Pendiente | Evidencia en `docs/tests/2026-08-11-sprint-2.md`. |
| 2026-08-11 | 3 | Ranking y resultados auditables | aceptado | Faltaban orden estable, version de esquema y escritura atomica | `65 passed` | Demo con esquema `1`; decisiones deterministas | Pendiente | Evidencia en `docs/tests/2026-08-11-sprint-3.md`. |
| 2026-08-11 | 4 | Decisiones y CV desde CLI | aceptado | No existía `botjobs.local_state` ni comandos locales | `76 passed` | Flujo `cv add` + `decisions set/list` aprobado | Pendiente | Evidencia en `docs/tests/2026-08-11-sprint-4.md`. |
| 2026-08-11 | 5 | Preparacion segura de postulaciones | aceptado | `--dry-run --browser` abría el navegador | `82 passed` | 6/6 casos de seguridad aprobados | Pendiente | Evidencia en `docs/tests/2026-08-11-sprint-5.md`. |
| 2026-08-11 | 6 | Envio controlado e idempotencia | aceptado | El registro ocurría después del navegador y dejaba una ventana de duplicación | `88 passed` | 7/7 casos de protocolo; sintaxis Node válida | Pendiente | Evidencia en `docs/tests/2026-08-11-sprint-6.md`. |
| 2026-08-11 | 7 | Empaque y entrega fisica | aceptado | El instalador ignoraba códigos de salida de procesos nativos | `95 passed` | Instalación limpia en ruta Unicode, `doctor` y demo exitosos | Pendiente | Evidencia en `docs/tests/2026-08-11-sprint-7.md`. |

## Registro de riesgos

| Riesgo | Mitigacion | Sprint propietario |
|---|---|---:|
| Cambios de HTML en portales | Fixtures, estados controlados y adaptadores aislados | 2 |
| Captcha o login | Perfil persistente e intervencion humana | 5 |
| Resultado JSON corrupto | Escritura atomica y respaldo | 3 |
| Envio duplicado | Idempotencia antes del clic final | 6 |
| Rutas o dependencias de la maquina | `doctor` y prueba en entorno limpio | 1 y 7 |
| Datos personales versionados | `.gitignore`, fixtures anonimizadas y revision de entrega | Todos |
