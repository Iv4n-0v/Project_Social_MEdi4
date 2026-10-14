# Microservicio de Analisis

Registra los analisis de redes sociales de cada usuario: sector, alcance
(`reach`) y tiempo en redes (`time_in_social_media`).
Borrado **logico**: eliminar un analisis pone `is_active=false` y se puede
recuperar con `/restore`. Cada cambio queda en la tabla de auditoria.

## Estructura (MVC por capas)

| MVC | Archivo | Responsabilidad |
|---|---|---|
| **Modelo** | `models.py`, `repository.py` | Tablas `analysis` y `analysis_audit`; unico lugar con consultas a la BD |
| **Vista** | `schemas.py` | Lo que recibe y expone la API (la "vista" de un servicio JSON) |
| **Controlador** | `router.py`, `service.py` | `router`: traduce HTTP; `service`: reglas de negocio y auditoria |
| Soporte | `database.py`, `main.py` | Conexion (`DATABASE_URL`), app, `/health` y errores de dominio -> HTTP |

Flujo: `router -> service -> repository -> BD`.

## La relacion analisis -> usuario

Cada analisis guarda el `user_id` de quien lo hizo. Como los usuarios viven en
**otro servicio** (con su propia BD), aqui es solo un numero, sin llave foranea:

```
analysis (id, sector, reach, time_in_social_media, user_id <- solo el ID, date, is_active)
```

Para mostrar un analisis con los datos del usuario, quien consume el servicio
pide `GET /analysis/{id}` y luego `GET /users/{user_id}` al servicio de usuarios.
`GET /analysis/?user_id=3` devuelve los analisis de un usuario.

## Endpoints (prefijo `/analysis`)

| Metodo | Ruta | Descripcion |
|---|---|---|
| GET | `/` | Lista. `?is_active=true/false` activos / eliminados; `?user_id=N` de un usuario |
| POST | `/` | Crea (JSON: `sector`, `reach`, `time_in_social_media`, `user_id`) -> 201. La fecha la pone el servidor |
| GET | `/{id}` | Detalle |
| PUT | `/{id}` | Actualizacion parcial (`sector`, `reach`, `time_in_social_media`). `user_id` no se cambia |
| DELETE | `/{id}` | Borrado logico |
| POST | `/{id}/restore` | Recupera un analisis eliminado |
| GET | `/{id}/audits` | Historial (CREATE, UPDATE, DELETE, RESTORE) |
| GET | `/health` | Healthcheck |

Errores: `404` analisis inexistente; `422` datos invalidos (sector vacio o de
mas de 100 caracteres, `reach` o `time_in_social_media` negativos, `user_id`
no positivo).

## Variables de entorno

| Variable | Uso |
|---|---|
| `DATABASE_URL` | BD (Postgres en Render). Si falta: `sqlite:///analysis.sqlite3` |

## Ejecutar

```bash
cd backend/microservicios/analisis
pip install -r requirements.txt
uvicorn main:app --reload --port 8004
```

Puertos: beneficios 8001, usuarios 8002, metodologias 8003, analisis 8004.

## Pruebas

```bash
pip install -r requirements-dev.txt
python -m pytest -v
```

Usan una BD en memoria: no tocan datos reales.

## Cambios respecto al servicio original

- Ya no usa SQLite fijo: lee `DATABASE_URL`.
- Capas separadas (router / service / repository) en vez de todo en el router.
- `DELETE` ahora es borrado logico (antes destruia el registro) y se agrega
  `/restore` y `/audits`.
- `PUT` y `PATCH` se unifican en un solo `PUT` parcial (igual que los otros servicios).

## Limitaciones conocidas

- `user_id` **no se valida** contra el servicio de usuarios (el monolito si lo
  hacia con `session.get(User, user_id)`): se puede guardar un ID inexistente.
  Pendiente: validarlo por HTTP a traves del gateway.
- No hay migracion de datos desde el monolito.
