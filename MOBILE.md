# BotJobs Mobile

La app movil esta construida con Expo y React Native. Consume exclusivamente las acciones permitidas por FastAPI y muestra los resultados JSON como vistas nativas.

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

### Paso 2 - CV y cartas dentro de la aplicacion

Estado: pendiente.

- Agregar una vista `Documentos` en la app.
- Subir uno o varios CV en PDF al backend local.
- Listar, consultar y seleccionar el CV activo que se enviara.
- Consultar las cartas generadas desde la app, sin mostrar rutas de Windows.
- Guardar metadatos locales con identificadores estables como `cv_id` y `carta_id`.
- Asociar cada vacante con `cv_id` y `carta_id`, no con rutas del sistema operativo.
- Permitir previsualizar y descargar el CV o la carta seleccionada.
- Mantener los archivos sensibles locales y validar tipo, tamano y nombre al subirlos.

La automatizacion de aplicaciones no debe comenzar hasta completar este paso y validar que cada vacante autorizada tenga documentos accesibles desde la app.

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
