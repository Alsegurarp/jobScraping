# Fase 2 - Automatizacion de aplicacion

## Objetivo

La Fase 2 convierte el compendio de vacantes en un flujo de aplicacion asistida. El sistema debe usar las vacantes ya rankeadas, las cartas generadas y el CV local para preparar aplicaciones, registrar avances y aplicar solo cuando exista autorizacion explicita del usuario.

La regla central es simple: ninguna vacante se envia sin autorizacion.

## Punto de partida

La Fase 1 ya entrega:

- Vacantes detectadas en `.xlsx`.
- Ranking por perfil.
- Vacantes preseleccionadas y descartadas.
- Cartas `.md` para vacantes preseleccionadas.
- Estados de extraccion e intervencion manual.
- URLs descartadas para ignorar en corridas futuras.

La Fase 2 debe leer esa salida y avanzar sobre las vacantes que el usuario apruebe.

## Alcance inicial

Primera version de Fase 2:

- Leer `output/botjobs_resultados.xlsx`.
- Detectar vacantes `preseleccionada`.
- Requerir una marca explicita `autorizar_aplicacion=si`.
- Abrir la vacante con navegador automatizado.
- Detectar boton o flujo de aplicacion.
- Cargar CV cuando exista campo de archivo.
- Pegar carta o mensaje corto cuando exista campo de texto.
- Detenerse antes del envio final si no se usa una bandera explicita de envio.
- Registrar resultado de cada intento en el `.xlsx`.

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

## Nuevas columnas propuestas

Agregar al workbook:

- `autorizar_aplicacion`: `si` o `no`.
- `estado_aplicacion`: `pendiente`, `autorizada`, `preparada`, `aplicada`, `fallida`, `requiere_intervencion`, `omitida`.
- `fecha_aplicacion`: fecha/hora del intento o envio.
- `portal_aplicacion`: portal donde se intento aplicar.
- `cv_usado`: ruta o nombre del CV enviado.
- `carta_usada`: ruta de la carta usada.
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
python .\bot_jobs.py --apply-approved --profile .\profile.example.json --jobs .\output\botjobs_resultados.xlsx --dry-run
```

Modo asistido con navegador, sin enviar:

```powershell
python .\bot_jobs.py --apply-approved --profile .\profile.example.json --jobs .\output\botjobs_resultados.xlsx --browser
```

Modo con envio final habilitado:

```powershell
python .\bot_jobs.py --apply-approved --profile .\profile.example.json --jobs .\output\botjobs_resultados.xlsx --browser --submit
```

`--submit` solo debe actuar sobre vacantes con:

- `estado=preseleccionada`
- `autorizar_aplicacion=si`
- carta existente
- CV existente
- sin captcha/login/bloqueo activo

## Flujo recomendado

1. Ejecutar Fase 1 con `--auto-search`.
2. Revisar `preseleccionadas` en el `.xlsx`.
3. Marcar manualmente `autorizar_aplicacion=si` solo en las vacantes aprobadas.
4. Ejecutar `--apply-approved --dry-run`.
5. Revisar el reporte de vacantes que se intentarian aplicar.
6. Ejecutar `--apply-approved --browser`.
7. Resolver manualmente login/captcha si aparece.
8. Revisar formularios preparados.
9. Enviar manualmente o ejecutar despues con `--submit`.
10. Revisar `estado_aplicacion` y `resultado_aplicacion` en el `.xlsx`.

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

1. Agregar columnas de aplicacion al contrato de workbook.
2. Agregar comando `--apply-approved` en modo `--dry-run`.
3. Crear hoja o seccion de seguimiento de aplicaciones.
4. Implementar lectura de vacantes autorizadas.
5. Validar existencia de CV y carta antes de intentar aplicar.
6. Crear modulo `botjobs/apply`.
7. Implementar aplicador base que abre URL y detecta barreras.
8. Implementar primer portal en modo asistido, recomendado LinkedIn o Glassdoor por facilidad de deteccion de URLs reales.
9. Registrar evidencia y resultado por intento.
10. Agregar `--submit` como bandera separada y bloqueada por autorizacion.
11. Repetir portal por portal.
12. Agregar metricas de aplicaciones: preparadas, aplicadas, fallidas e intervenciones.

## Criterio de exito

La Fase 2 se considera util cuando:

- El usuario puede marcar vacantes aprobadas en el Excel.
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
