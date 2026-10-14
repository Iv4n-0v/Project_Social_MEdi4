# Microservicio de Beneficios

Gestiona el catalogo de beneficios. Borrado **logico**: eliminar un beneficio
pone `is_active=false` y se puede recuperar con `/restore`. Cada cambio queda
en la tabla de auditoria.

## Estructura (MVC por capas)

| MVC | Archivo | Responsabilidad |
|---|---|---|
| **Modelo** | `models.py`, `repository.py` | Tablas `benefits` y `benefit_audit`; unico lugar con consultas a la BD |
| **Vista** | `schemas.py` | Lo que recibe y expone la API (la "vista" de un servicio JSON) |
| **Controlador** | `router.py`, `service.py` | `router`: traduce HTTP; `service`: reglas de negocio y auditoria |
| Soporte | `database.py`, `main.py` | Conexion (`DATABASE_URL`), app, `/health` y errores de dominio -> HTTP |

Flujo: `router -> service -> repository -> BD`.

## Endpoints (prefijo `/benefits`)

| Metodo | Ruta | Descripcion |
|---|---|---|
| GET | `/` | Lista. `?is_active=true/false` y/o `?ids=1,2,3` |
| POST | `/` | Crea (JSON: `name`, `description` opcional) -> 201 |
| GET | `/{id}` | Detalle |
| PUT | `/{id}` | Actualizacion parcial (JSON). Un campo omitido no cambia |
| DELETE | `/{id}` | Borrado logico |
| POST | `/{id}/restore` | Recupera un beneficio eliminado |
| GET | `/{id}/audits` | Historial (CREATE, UPDATE, DELETE, RESTORE) |
| GET | `/health` | Healthcheck |

`?ids=` sirve para que otro servicio (o el gateway) pida solo los beneficios
que necesita, por ejemplo los `benefit_id` de una metodologia.

Errores: `404` beneficio inexistente, `422` datos invalidos (nombre vacio o de
mas de 100 caracteres, descripcion de mas de 500, `ids` mal formado).

## Variables de entorno

| Variable | Uso |
|---|---|
| `DATABASE_URL` | BD (Postgres en Render). Si falta: `sqlite:///benefits.sqlite3` |

## Ejecutar

```bash
cd backend/microservicios/beneficios
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

El puerto 8001 es el que ya usa el monolito (`backend/benefit.py`).

## Pruebas

```bash
pip install -r requirements-dev.txt
python -m pytest -v
```

Usan una BD en memoria: no tocan datos reales.

## Cambios respecto a la version anterior

- Crear responde **201** (antes 200). `backend/benefit.py` ya acepta ambos.
- `DELETE` ahora es borrado logico y devuelve el beneficio (antes borraba y
  devolvia un mensaje).
- `PUT` es parcial (antes exigia `name`).
- La tabla se llama `benefits` (antes `benefit`). No hay migracion de datos.
- Nombre maximo 100 caracteres; descripcion maxima 500.
