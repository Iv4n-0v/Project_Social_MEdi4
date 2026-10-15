#!/usr/bin/env bash
# Separa el frontend del backend de forma explicita en el codigo.
#   ANTES:  backend/ = frontend (rutas, services, clients) + microservicios ; templates/ y gateway/ en la raiz
#   DESPUES: frontend/ = app web (Jinja)   |   backend/ = microservicios + gateway
# Uso (desde cualquier carpeta del repo):  bash separar_frontend.sh
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

[ -f backend/main.py ] && [ -d backend/microservicios ] || { echo "ERROR: no encuentro backend/main.py y backend/microservicios. ¿Estas en el repo correcto y en la rama con todos los cambios?"; exit 1; }
[ ! -d frontend ] || { echo "ERROR: frontend/ ya existe (¿ya corriste este script?)"; exit 1; }
[ -z "$(git status --porcelain)" ] || { echo "ERROR: hay cambios sin commit. Haz commit (o descartalos) y vuelve a correr el script."; exit 1; }

echo "1/6 Moviendo archivos con git mv (conserva el historial)..."
mkdir frontend
for f in main user analysis benefit methodology reports models; do
  [ -f "backend/$f.py" ] && git mv "backend/$f.py" "frontend/$f.py"
done
git mv backend/clients frontend/clients
git mv backend/services frontend/services
git mv templates frontend/templates
git mv gateway backend/gateway
git mv Dockerfile.monolito frontend/Dockerfile
[ -f .dockerignore ] && git rm -q .dockerignore

echo "2/6 Actualizando imports (backend. -> frontend.)..."
find frontend -name '*.py' -print0 | xargs -0 sed -i -E 's/\bfrom backend\./from frontend./g; s/\bfrom backend import/from frontend import/g; s/\bimport backend\./import frontend./g'
# las plantillas ahora viven dentro de frontend/
sed -i -E 's|^BASE_DIR = .*|BASE_DIR = Path(__file__).resolve().parent  # carpeta frontend/|' frontend/main.py

echo "3/6 Archivos propios del frontend (Dockerfile, requirements, .dockerignore)..."
cat > frontend/requirements.txt <<'EOF'
# Solo lo que necesita el frontend (app web Jinja). Los micros tienen sus propios requirements.
fastapi==0.122.0
uvicorn==0.38.0
Jinja2==3.1.6
httpx==0.28.1
python-multipart==0.0.20
sqlmodel==0.0.27
reportlab==4.4.4
EOF
cat > frontend/Dockerfile <<'EOF'
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Primero las dependencias: si solo cambia el codigo, Docker reutiliza esta capa
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# El codigo queda en /app/frontend para que los imports "frontend.xxx" funcionen
COPY . ./frontend

RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "frontend.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
printf '__pycache__/\n*.pyc\n.env\nREADME.md\n' > frontend/.dockerignore

echo "4/6 Actualizando docker-compose.yml, rutas en documentos y .gitignore..."
python3 - <<'PY'
import re, pathlib
p = pathlib.Path("docker-compose.yml"); s = p.read_text(encoding="utf-8")
s = s.replace("./gateway/krakend/krakend.json", "./backend/gateway/krakend/krakend.json")
s = re.sub(r"  frontend:.*?\n    build:\n      context: \.\n      dockerfile: Dockerfile\.monolito\n",
           '  frontend:   # antes "monolito": app web sin datos ni BD (Vista Jinja + Controlador)\n    build: ./frontend\n', s, flags=re.S)
p.write_text(s, encoding="utf-8")
q = pathlib.Path("backend/gateway/krakend/README.md")
if q.exists():
    t = q.read_text(encoding="utf-8")
    t = t.replace("gateway/krakend", "backend/gateway/krakend").replace("backend/backend/", "backend/")
    t = t.replace("`backend/services/` del frontend", "`frontend/services/`").replace("`backend/benefit.py`", "`frontend/benefit.py`")
    q.write_text(t, encoding="utf-8")
g = pathlib.Path("backend/gateway/krakend/generate.py")
if g.exists():
    g.write_text(g.read_text(encoding="utf-8").replace("python gateway/krakend/generate.py", "python backend/gateway/krakend/generate.py"), encoding="utf-8")
PY

echo "5/6 README del frontend..."
cat > frontend/README.md <<'EOF'
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
EOF

echo "6/6 Verificando que compila..."
python3 -m py_compile frontend/*.py frontend/services/*.py frontend/clients/*.py
find frontend -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true

LEFT=$(ls backend | grep -v -x -e microservicios -e gateway -e __pycache__ || true)
if [ -n "$LEFT" ]; then
  echo
  echo "AVISO: quedaron archivos sueltos en backend/ que no son micros ni gateway:"
  echo "$LEFT"
  echo "(probablemente db.py o supa/, que ya no se usan: borralos con git rm -r si es el caso)"
fi
echo
echo "Listo. Revisa con:  git status --short"
echo "Luego:  docker compose up --build -d --remove-orphans"
echo "Si todo funciona:  git add -A && git commit -m 'Separar frontend y backend' && git push"
