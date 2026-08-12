# Checklist de entrega física

## Antes de entregar

- [ ] Confirmar versión `1.0.0`.
- [ ] Ejecutar `scripts/verify.ps1`.
- [ ] Confirmar suite completa en verde.
- [ ] Ejecutar `doctor` en la máquina destino.
- [ ] Verificar Python 3.10 o superior.
- [ ] Verificar Node y Chrome o Edge si se usará navegador.
- [ ] Crear perfil personalizado sin versionar secretos.
- [ ] Agregar y activar el CV correcto.
- [ ] Crear respaldo inicial.

## Prueba de aceptación

- [ ] Ejecutar demo.
- [ ] Buscar máximo cinco vacantes en un portal.
- [ ] Confirmar degradación controlada si el portal bloquea.
- [ ] Revisar ranking, flags y cartas.
- [ ] Registrar una decisión de prueba.
- [ ] Ejecutar aplicación en `--dry-run`.
- [ ] Preparar sin enviar y revisar evidencia.
- [ ] Restaurar un respaldo en un directorio de prueba.

## Seguridad

- [ ] `runtime/`, `output/`, `cache/`, `.env` y CV no aparecen en Git.
- [ ] No existen credenciales en documentación o consola compartida.
- [ ] El usuario entiende los estados `en_progreso`, `incierto` y `confirmado`.
- [ ] El envío real requiere `ENVIAR` y revisión humana.
