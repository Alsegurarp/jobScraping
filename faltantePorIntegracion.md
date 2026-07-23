# Faltante por integracion

## Objetivo de cierre

BotJobs se considera finalizado como MVP cuando pueda preparar y enviar, de forma controlada, una vacante aprobada en cada portal soportado, conservar la sesion y registrar el resultado sin riesgo de duplicados.

## Prioridad P0 — Implementacion completada

Orden obligatorio de ejecución:

1. **P0.1 — Sesiones e intervención manual:** habilita pruebas reales sin reiniciar el flujo.
2. **P0.2 — Adaptadores por portal:** prepara formularios de forma confiable.
3. **P0.3 — Envío final seguro:** se habilita únicamente sobre adaptadores verificados.

La implementación local de P0 está completa. La validación real por portal requiere cuentas, sesiones y vacantes reales aprobadas.

## P0.1 — Sesiones e intervencion manual

Estado: implementado.

- Usar un perfil persistente de navegador por portal para conservar sesiones autorizadas.
- Permitir que el usuario resuelva login, captcha o verificación humana.
- Reanudar la misma aplicación después de la intervención.
- Conservar el estado y los materiales ya preparados.
- Agregar reintento explícito para aplicaciones en `requiere_intervencion`.
- No automatizar evasión de captcha ni controles de seguridad.

Criterio de terminado: pausar ante una barrera, resolverla manualmente y continuar sin reiniciar la aplicación.

## P0.2 — Adaptadores por portal

Estado: implementados los cinco adaptadores; pendiente validación operativa con una vacante real por portal.

Implementar y verificar adaptadores específicos para:

1. LinkedIn: primera integración y patrón de referencia.
2. Indeed.
3. OCC.
4. Computrabajo.
5. Glassdoor.

Cada adaptador debe:

- Reconocer el portal y localizar el flujo real de postulacion.
- Detectar campos obligatorios, CV, carta y preguntas adicionales.
- Cargar el CV seleccionado y la carta correspondiente.
- Detenerse ante captcha, login, bloqueo o campos desconocidos.
- Devolver un resultado uniforme: `preparada`, `fallida` o `requiere_intervencion`.
- Guardar URL final, motivo y captura como evidencia.

Criterio de terminado por portal: preparar correctamente al menos una postulación real sin enviarla. No avanzar al portal siguiente hasta cumplirlo.

## P0.3 — Envio final seguro

Estado: implementado con confirmación literal, dominio permitido, autorización, materiales válidos e idempotencia.

- Habilitar `--submit` únicamente para adaptadores verificados.
- Exigir `decision_usuario=aprobada`, CV válido, carta existente y formulario compatible.
- Mostrar o registrar una confirmacion explícita antes del envío.
- Crear una clave idempotente por vacante para impedir envíos duplicados.
- Confirmar el éxito desde la respuesta o página final del portal.
- Registrar `aplicada`, `fallida` o `requiere_intervencion`, junto con fecha y evidencia.
- Mantener el envío bloqueado ante cualquier estado ambiguo.

Criterio de terminado por portal: realizar un envío controlado, comprobar su confirmación y demostrar que un segundo intento queda bloqueado.

## P1 — App movil

Estado: implementado.

- Pantalla específica de Documentos.
- Selección de CV diferente por vacante.
- Estados, resultados y capturas de aplicaciones visibles.
- Confirmación explícita antes de solicitar un envío.

## P1 — Historial y metricas

Estado: implementado.

- El historial se conserva aunque se ejecute una búsqueda nueva.
- Se muestran autorizadas, preparadas, aplicadas, fallidas e intervenciones.
- Los intentos quedan registrados y los duplicados se bloquean.

## P1 — Validacion final

Estado: validación local completada; pendiente validación externa con cuentas y vacantes reales.

- Ejecutar una búsqueda pequeña real en cada portal.
- Preparar una aplicación real por portal.
- Verificar CV, carta, campos y evidencia.
- Ejecutar un envío controlado por cada adaptador antes de declararlo estable.
- Dejar pruebas automatizadas para autorización, idempotencia y estados.

## Fuera del cierre del MVP

Estas integraciones pueden realizarse después:

- Redacción con IA.
- Google Sheets.
- Emails automáticos a reclutadores.
- Aprendizaje histórico de descartes.
