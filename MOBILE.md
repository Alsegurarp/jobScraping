# BotJobs Mobile

La app movil esta construida con Expo y React Native. Consume exclusivamente las acciones permitidas por FastAPI y muestra los resultados JSON como vistas nativas.

La pestaña `Documentos` permite subir, consultar y activar CV. En `Resultados` puede elegirse un CV específico por vacante; si no se elige, se usa el CV activo. La vista `Seguimiento` muestra estados y evidencias. El envío exige confirmación explícita.

## Portales incluidos en el MVP

- Indeed.
- OCC.
- Computrabajo.
- Glassdoor.

LinkedIn fue retirado del selector móvil porque Cloudflare lo mantiene en `requiere_intervencion`. Los ajustes específicos para recuperarlo quedan para una versión futura. Durante el MVP, cualquier portal bloqueado de la misma forma debe documentarse y retirarse del selector móvil.

## 1. Iniciar el backend para la red local

Desde la raiz del proyecto:

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

`0.0.0.0` permite que un telefono en la misma red Wi-Fi se conecte. El backend sigue disponible en la PC mediante `http://127.0.0.1:8000`.

## 2. Configurar la URL

Consulta la IP Wi-Fi de la PC:

```powershell
ipconfig
```

Crea `mobile/.env` a partir de `mobile/.env.example` y usa esa IP:

```text
EXPO_PUBLIC_API_URL=http://TU_IP_WIFI:8000
```

El archivo `.env` es local y esta ignorado por Git. Reinicia Expo despues de cambiarlo.

## 3. Iniciar Expo

```powershell
cd .\mobile
npm install
npx expo start
```

Escanea el codigo QR con Expo Go. La PC y el telefono deben estar en la misma red. Para abrir la version web:

```powershell
npm run web
```

## Funciones

### Ejecutar

- Seleccionar uno o varios portales.
- Definir entre 1 y 50 resultados.
- Activar actualizacion de cache, navegador e investigacion.
- Iniciar busqueda automatica.
- Extraer links desde `vacantes.template.xlsx`.
- Comprobar la conexion con FastAPI.
- Lanzar el placeholder de simulacion de Fase 2.

La simulacion de aplicaciones queda registrada como fallida mientras el CLI no implemente `--apply-approved --dry-run`. No aplica a ninguna vacante.

### Resultados

- Resumen de ejecucion.
- Vacantes detectadas.
- Preseleccionadas.
- Descartadas.
- Aplicadas.
- Requieren intervencion humana.

Cada vacante se muestra como una tarjeta compacta. Al expandirla aparecen solo los datos utiles para decidir o intervenir. La URL se usa internamente en el boton `Abrir vacante`, pero no se repite como texto. Las rutas locales de CV y cartas tampoco se muestran.

### Historial

Muestra las corridas registradas y sus estados. Las busquedas y extracciones completadas guardan una copia en `runtime/results/{run_id}.json`, por lo que abrir una corrida anterior conserva sus resultados originales.

## Roadmap de la app

### Paso 1 - Busqueda y resultados JSON

Estado: implementado.

- Ejecutar busquedas y extracciones controladas.
- Consultar resumen, detectadas, preseleccionadas, descartadas, aplicadas e intervenciones.
- Consultar historial por `run_id`.
- Abrir la URL de una vacante desde su boton.
- Consultar la carta generada desde `Ver carta de empleo` en cada vacante preseleccionada.

### Paso 2 - CV y cartas dentro de la aplicacion

Estado: en progreso.

Implementado:

- Subir uno o varios CV en PDF desde la pantalla `Resultados`.
- Listar los CV guardados localmente.
- Consultar cada PDF con `Ver CV`.
- Seleccionar el CV activo que se enviara.
- Guardar metadatos locales con identificadores estables como `cv_id` y `carta_id`.

Pendiente, como tareas separadas:

- Agregar una vista general `Documentos` si resulta necesaria despues de validar el flujo en `Resultados`.
- Agregar una biblioteca general para consultar y administrar todas las cartas, ademas del visor por vacante ya implementado.
- Asociar cada vacante con `cv_id` y `carta_id`, no con rutas del sistema operativo.
- Permitir previsualizar y descargar el CV o la carta seleccionada.
- Mantener los archivos sensibles locales y validar tipo, tamano y nombre al subirlos.

### Paso 3 - Decision manual por vacante

Estado: implementado.

- Cada vacante con URL puede marcarse como `Aprobar`, `Descartar` o `Revisar`.
- La decision se guarda localmente en el backend por URL de vacante.
- Al volver a consultar resultados, la decision aparece como `decision_usuario`.

La automatizacion de aplicaciones no debe comenzar hasta validar que cada vacante aprobada tenga CV activo y carta accesible desde la app.

## Verificacion

Backend:

```powershell
python -m pytest
```

Frontend:

```powershell
cd .\mobile
npx tsc --noEmit
npx expo export --platform web
```
