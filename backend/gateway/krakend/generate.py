"""Genera krakend.json (Docker) y krakend.local.json (sin Docker).

Los 4 microservicios exponen el mismo CRUD, asi que en vez de copiar 40
endpoints a mano se describen una vez y se generan. Uso:

    python backend/gateway/krakend/generate.py

KrakenD solo lee los .json generados; este script es una comodidad.
"""
import json
from pathlib import Path

# nombre -> (ruta publica, ruta del micro, puerto, query strings permitidos)
SERVICES = {
    "beneficios": ("benefits", "/benefits", 8001, ["is_active", "ids"]),
    "usuarios": ("users", "/users", 8002, ["is_active"]),
    "metodologias": ("methodologies", "/methodologies", 8003, ["is_active"]),
    "analisis": ("analysis", "/analysis", 8004, ["is_active", "user_id"]),
}

# (metodo, sufijo publico, sufijo en el micro, lleva {id}?, es subida de archivos?)
# La coleccion lleva "/" final porque FastAPI la define asi (evita un 307).
OPERATIONS = [
    ("GET", "", "/", False, False),
    ("POST", "", "/", False, False),
    ("GET", "/{id}", "/{id}", True, False),
    ("PUT", "/{id}", "/{id}", True, False),
    ("DELETE", "/{id}", "/{id}", True, False),
    ("POST", "/{id}/restore", "/{id}/restore", True, False),
    ("GET", "/{id}/audits", "/{id}/audits", True, False),
]
# Solo usuarios: crear con imagen (multipart) y cambiar imagen
UPLOAD_TIMEOUT = "30s"


def endpoint(method, public, backend_path, host, query, timeout=None):
    ep = {
        "endpoint": public,
        "method": method,
        "output_encoding": "no-op",  # pasa tal cual codigo, cuerpo y errores del micro
        "input_query_strings": query if method == "GET" else [],
        # Content-Type es obligatorio para que el micro entienda JSON o multipart
        "input_headers": ["Content-Type", "Accept"],
        "backend": [
            {
                "url_pattern": backend_path,
                "method": method,
                "host": [host],
                "encoding": "no-op",
            }
        ],
    }
    if timeout:
        ep["timeout"] = timeout
    return ep


def build(hosts):
    endpoints = []
    for name, (public, prefix, _port, query) in SERVICES.items():
        host = hosts[name]
        for method, pub_suffix, back_suffix, _, _ in OPERATIONS:
            pub = f"/api/v1/{public}{pub_suffix}"
            back = f"{prefix}{back_suffix}"
            timeout = UPLOAD_TIMEOUT if (name == "usuarios" and method in ("POST", "PUT") and pub_suffix == "") else None
            endpoints.append(endpoint(method, pub, back, host, query, timeout))
        if name == "usuarios":
            endpoints.append(
                endpoint("PUT", "/api/v1/users/{id}/image", "/users/{id}/image", host, [], UPLOAD_TIMEOUT)
            )
    return {
        "$schema": "https://www.krakend.io/schema/krakend.json",
        "version": 4,
        "name": "Project Social Media - API Gateway",
        "port": 8080,
        "timeout": "10s",
        "cache_ttl": "0s",
        "endpoints": endpoints,
    }


if __name__ == "__main__":
    here = Path(__file__).parent
    docker_hosts = {n: f"http://{n}:{s[2]}" for n, s in SERVICES.items()}
    local_hosts = {n: f"http://127.0.0.1:{s[2]}" for n, s in SERVICES.items()}
    for filename, hosts in (("krakend.json", docker_hosts), ("krakend.local.json", local_hosts)):
        cfg = build(hosts)
        (here / filename).write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
        print(f"{filename}: {len(cfg['endpoints'])} endpoints")
