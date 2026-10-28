# Frontend React (Vite + nginx)

Reemplaza el frontend FastAPI + Jinja2. Es una capa web que no tiene base de datos ni lógica de negocio:
solo consume el API Gateway (KrakenD) en `/api/v1`.

## Cómo está organizado (MVC)
- Vista: `src/components` y `src/pages` (componentes React)
- Controlador: `CrudPage.jsx` (estado y acciones de cada pantalla)
- Modelo / acceso a datos: `src/api` (Adapter sobre `fetch`) y `src/config/resources.js`
- Archivo de excepciones: `src/api/errors.js` (`ApiError`, `NetworkError`, `friendlyMessage`)
- Colorimetría: variables de color en `src/styles.css` (`:root`)

## Desarrollo local
1. Levantar el gateway y los microservicios (puerto 8080).
2. `npm install`
3. `npm run dev` y abrir http://localhost:5173 (Vite redirige /api a localhost:8080).

## Docker
En `docker-compose.yml`, reemplazar el servicio `frontend` por:

```yaml
  frontend:
    build: ./frontend-react
    ports:
      - "8000:8080"
    depends_on:
      - gateway
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:8080/health"]
      interval: 10s
      timeout: 3s
      retries: 5
```

nginx sirve los archivos compilados y reenvía `/api/` al gateway, por eso no hace falta CORS.
La imagen `nginx-unprivileged` no corre como root.
