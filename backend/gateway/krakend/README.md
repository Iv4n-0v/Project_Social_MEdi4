# API Gateway (KrakenD)

Unica puerta de entrada a los microservicios. El monolito (y luego el front)
llaman a `http://<gateway>:8080/api/v1/...` y KrakenD reenvia al servicio
correcto. **Nadie llama a los micros directamente.**

```
monolito / navegador ──► KrakenD :8080 ──► beneficios   :8001
                                       ├─► usuarios      :8002
                                       ├─► metodologias  :8003
                                       └─► analisis      :8004
```

## Archivos

| Archivo | Uso |
|---|---|
| `krakend.json` | Con Docker: los hosts son los nombres de servicio (`http://beneficios:8001`) |
| `krakend.local.json` | Sin Docker: los hosts son `http://127.0.0.1:800X` |
| `generate.py` | Genera los dos JSON (los 4 micros comparten el mismo CRUD) |

Si cambias algo, edita `generate.py` y ejecuta `python backend/gateway/krakend/generate.py`.

## Rutas publicas (`/api/v1`)

Cada recurso (`benefits`, `users`, `methodologies`, `analysis`) expone:

| Metodo | Ruta | Micro |
|---|---|---|
| GET / POST | `/api/v1/{recurso}` | lista / crea |
| GET / PUT / DELETE | `/api/v1/{recurso}/{id}` | detalle / actualiza / borrado logico |
| POST | `/api/v1/{recurso}/{id}/restore` | recupera |
| GET | `/api/v1/{recurso}/{id}/audits` | historial |
| PUT | `/api/v1/users/{id}/image` | solo usuarios: cambia la imagen |

Filtros por query string permitidos: `is_active` (todos), `ids` (beneficios),
`user_id` (analisis). KrakenD **descarta** cualquier query string que no este
declarada, por eso estan listadas en el JSON.
Ademas: `GET /__health` (propio de KrakenD).

## Decisiones (para el archivo de decisiones)

- **Patron Facade / API Gateway**: un solo punto de entrada que oculta cuantos
  servicios hay y donde viven. Si un micro cambia de puerto o de host, el
  cliente no se entera.
- **`no-op`**: KrakenD no interpreta el JSON, solo lo reenvia. Asi se conservan
  los codigos de error del micro (404, 422...) con su `detail`, y funciona la
  subida de imagenes `multipart/form-data` de usuarios.
- **Versionado `/api/v1`**: permite cambiar la API sin romper a los clientes.
- **Timeout 10 s** global y **30 s** para subir imagenes (Render gratis tarda en
  "despertar").
- **Sin barra final**: `/api/v1/benefits`, no `/api/v1/benefits/`.
- **No se compone nada en el gateway** (p. ej. metodologia + datos de sus
  beneficios): eso se hace en `backend/services/` del monolito con 2 llamadas
  (`GET /api/v1/methodologies/1` y `GET /api/v1/benefits?ids=1,2`).
  KrakenD CE podria, pero su propia documentacion lo desaconseja para este caso.
- Pendiente: autenticacion (JWT del futuro microservicio de login) y CORS si el
  front llama al gateway desde el navegador.

## Probar

1. Levanta los 4 micros (cada uno en su carpeta, con su puerto).
2. Valida y arranca KrakenD (necesita Docker; desde la raiz del repo):

```bash
docker run --rm -v "$PWD/backend/gateway/krakend:/etc/krakend" krakend:latest check -c /etc/krakend/krakend.local.json
docker run --rm --network host -v "$PWD/backend/gateway/krakend:/etc/krakend" krakend:latest run -c /etc/krakend/krakend.local.json
```

(`--network host` hace que `127.0.0.1` sea tu maquina; en Codespaces funciona.)

3. Prueba:

```bash
curl -i localhost:8080/__health
curl -i -X POST localhost:8080/api/v1/benefits -H 'Content-Type: application/json' -d '{"name":"Ingresos pasivos"}'
curl -i localhost:8080/api/v1/benefits?is_active=true
curl -i localhost:8080/api/v1/benefits/999        # 404 con "Benefit not found"
curl -i localhost:8080/api/v1/analysis?user_id=1
```

## Monolito

`frontend/benefit.py` ahora lee `GATEWAY_URL` (por defecto `http://127.0.0.1:8080`)
y llama a `/api/v1/benefits`. El `gateway/main.py` viejo (FastAPI + httpx) ya no
hace falta y se puede borrar cuando esto funcione.
