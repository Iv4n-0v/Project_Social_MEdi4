# Frontend (app web)

Interfaz web del proyecto. **No tiene base de datos ni logica de negocio**: todo
dato sale de los microservicios, siempre a traves del gateway (KrakenD).

```
navegador ─► frontend :8000 ─► gateway :8080 ─► micros (backend/microservicios)
```

| MVC | Carpeta | Responsabilidad |
|---|---|---|
| **Vista** | `templates/` | HTML (Jinja2) |
| **Controlador** | `main.py`, `user.py`, `analysis.py`, `benefit.py`, `methodology.py`, `reports.py` | Reciben la peticion y eligen la plantilla |
| Servicios | `services/` | Coordinan clientes y componen datos de varios micros |
| Clientes | `clients/` | Hablan HTTP con el gateway (patron Adapter) |
| Esquemas | `models.py` | Validan lo que llega por las rutas (ya no hay tablas) |

## Ejecutar

Con Docker (todo el sistema): `docker compose up --build` desde la raiz del repo.

Sin Docker (con el gateway y los micros ya corriendo), desde la raiz del repo:
```bash
pip install -r frontend/requirements.txt
GATEWAY_URL=http://127.0.0.1:8080 uvicorn frontend.main:app --reload --port 8000
```

`GATEWAY_URL` por defecto es `http://127.0.0.1:8080`.
