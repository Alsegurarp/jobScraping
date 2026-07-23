# Fase 2 - Automatizacion de aplicacion

## Objetivo

La Fase 2 convierte los resultados JSON en un flujo de aplicacion asistida. El sistema debe usar las vacantes ya rankeadas y documentos administrados desde la app para preparar aplicaciones, registrar avances y aplicar solo cuando exista autorizacion explicita del usuario.

La regla central es simple: ninguna vacante se envia sin autorizacion.

## Punto de partida

La Fase 1 ya entrega:

- Vacantes detectadas en `output/botjobs_resultados.json`.
- Ranking por perfil.
- Vacantes preseleccionadas y descartadas.
- Cartas `.md` para vacantes preseleccionadas.
- Estados de extraccion e intervencion manual.
- URLs descartadas para ignorar en corridas futuras.

La Fase 2 debe leer esa salida y avanzar sobre las vacantes que el usuario apruebe.

## Alcance inicial

Primera version de Fase 2:

- Leer `output/botjobs_resultados.json`.
- Permitir subir y consultar CV y cartas desde la app antes de preparar aplicaciones.
- Detectar vacantes `preseleccionada`.
- Requerir una marca explicita `autorizar_aplicacion=si`.
- Abrir la vacante con navegador automatizado.
- Detectar boton o flujo de aplicacion.
- Cargar CV cuando exista campo de archivo.
- Pegar carta o mensaje corto cuando exista campo de texto.
- Detenerse antes del envio final si no se usa una bandera explicita de envio.
- Registrar resultado de cada intento en JSON.

## Fuera de alcance inicial

No debe implementarse al inicio:

- Evasion de captchas.
- Evasion de login.
- Aplicacion sin autorizacion.
- Envio masivo sin revision.
- Envio de emails automatico.
- Sincronizacion directa con Google Sheets.
- Modificacion automatica del CV.

Si aparece captcha, login o verificacion humana, el bot debe pausar y registrar `requiere_intervencion`.

## Nuevos campos propuestos

Agregar al contrato JSON:

- `autorizar_aplicacion`: `si` o `no`.
- `estado_aplicacion`: `pendiente`, `autorizada`, `preparada`, `aplicada`, `fallida`, `requiere_intervencion`, `omitida`.
- `fecha_aplicacion`: fecha/hora del intento o envio.
- `portal_aplicacion`: portal donde se intento aplicar.
- `cv_id`: identificador del CV administrado por la app.
- `carta_id`: identificador de la carta administrada por la app.
- `mensaje_usado`: mensaje corto usado, si aplica.
- `requiere_confirmacion_envio`: `si` o `no`.
- `resultado_aplicacion`: descripcion corta del resultado.
- `evidencia_aplicacion`: captura, URL final o nota operativa.
- `notas_aplicacion`: observaciones manuales.

## Estados de aplicacion

- `pendiente`: vacante preseleccionada, pero no autorizada.
- `autorizada`: marcada por el usuario para intentar aplicar.
- `preparada`: el bot abrio la vacante, cargo materiales o dejo el formulario listo.
- `aplicada`: aplicacion enviada correctamente.
- `fallida`: intento fallido por error tecnico o formulario incompatible.
- `requiere_intervencion`: necesita login, captcha, confirmacion humana o dato no disponible.
- `omitida`: no se intento aplicar por reglas del perfil, falta de carta, falta de CV o autorizacion ausente.

## Comandos propuestos

Modo seco para revisar que aplicaria:

```powershell
python .\bot_jobs.py --apply-approved --profile .\profile.example.json --jobs .\output\botjobs_resultados.json --dry-run
```

Modo asistido con navegador, sin enviar:

```powershell
python .\bot_jobs.py --apply-approved --profile .\profile.example.json --jobs .\output\botjobs_resultados.json --browser
```

Modo con envio final habilitado:

```powershell
python .\bot_jobs.py --apply-approved --profile .\profile.example.json --jobs .\output\botjobs_resultados.json --browser --submit
```

`--submit` solo debe actuar sobre vacantes con:

- `estado=preseleccionada`
- `autorizar_aplicacion=si`
- carta existente
- CV existente
- sin captcha/login/bloqueo activo

## Flujo recomendado

1. Ejecutar Fase 1 con `--auto-search`.
2. Revisar `preseleccionadas` en la app.
3. Subir o seleccionar el CV y consultar la carta desde `Documentos`.
4. Autorizar desde la app solo las vacantes aprobadas.
5. Ejecutar `--apply-approved --dry-run`.
6. Revisar el reporte de vacantes que se intentarian aplicar.
7. Ejecutar `--apply-approved --browser`.
8. Resolver manualmente login/captcha si aparece.
9. Revisar formularios preparados.
10. Enviar manualmente o ejecutar despues con `--submit`.
11. Revisar `estado_aplicacion` y `resultado_aplicacion` en la app.

## Estructura tecnica propuesta

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

Responsabilidades:

- `runner.py`: lee vacantes aprobadas, coordina portal y actualiza resultados.
- `common.py`: utilidades compartidas de navegador, carga de CV, captura de evidencia y estados.
- Archivos por portal: detectan botones, formularios, campos y barreras especificas.

## Roadmap Fase 2

1. Agregar campos de aplicacion al contrato JSON. Estado: implementado.
2. Implementar `Documentos` para subir y consultar CV y cartas desde la app. Estado: implementado.
3. Agregar comando `--apply-approved` en modo `--dry-run`. Estado: implementado.
4. Crear una seccion JSON de seguimiento de aplicaciones. Estado: implementado como `aplicaciones`.
5. Implementar lectura de vacantes autorizadas. Estado: implementado para decisiones `aprobada`.
6. Validar existencia de CV y carta antes de intentar aplicar. Estado: implementado.
7. Crear modulo de aplicacion. Estado: implementado inicialmente en `botjobs/apply.py`.
8. Implementar aplicador base que abre URL y detecta barreras. Estado: implementado; detecta barreras, boton de aplicacion, archivo y texto.
9. Implementar primer portal en modo asistido. Estado: implementados adaptadores iniciales para los cinco portales; pendiente validacion real.
10. Registrar evidencia y resultado por intento. Estado: implementado con captura PNG y resultado estructurado.
11. Agregar `--submit` como bandera separada y bloqueada por autorizacion. Estado: implementado; requiere `--confirm-submit ENVIAR` y registro idempotente.
12. Repetir portal por portal. Estado: implementacion inicial completa; pendiente prueba operativa por portal.
13. Agregar metricas de aplicaciones: preparadas, aplicadas, fallidas e intervenciones. Estado: implementado.

## Criterio de exito

La Fase 2 se considera util cuando:

- El usuario puede autorizar vacantes desde la app.
- El CV y la carta seleccionados se consultan desde la app mediante identificadores, no rutas locales.
- El bot identifica solo esas vacantes.
- El bot abre cada oferta y prepara materiales.
- El bot registra claramente si la aplicacion quedo preparada, aplicada, fallida o requiere intervencion.
- No existe riesgo de aplicar a una vacante no aprobada.

## Integraciones futuras relacionadas

- Sesiones persistentes por portal para no iniciar sesion en cada corrida.
- Reintento automatico de vacantes `requiere_intervencion` despues de resolver login/captcha.
- Sincronizacion con Google Sheets.
- Envio de email a reclutadores cuando la vacante incluya correo.
- Uso de IA para adaptar carta, mensaje y resumen de experiencia antes de enviar.
- Seleccion automatica entre multiples versiones de CV.
- Capturas de pantalla como evidencia visual de aplicacion.
