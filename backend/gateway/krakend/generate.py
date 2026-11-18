"""Genera krakend.json (Docker) y krakend.local.json (sin Docker).

El servicio de autenticacion (8005) se describe aparte (AUTH_OPERATIONS).
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

# Servicio de emprendimientos (puerto 8006): catalogo publico, "mi emprendimiento" y favoritos.
VENTURES_PORT = 8006

# Servicio de autenticacion (puerto 8005). Las rutas son distintas al CRUD, por eso
# se describen aparte. El JWT se valida AQUI, en el gateway, con la llave publica
# que el servicio auth publica en /.well-known/jwks.json (sin secretos compartidos).
AUTH_PORT = 8005
JWT_ISSUER = "social-media-auth"
JWT_AUDIENCE = "social-media-api"
ROLES = ["visitor", "entrepreneur"]

# True = los CRUD (usuarios, metodologias, beneficios, analisis) exigen un token con rol
# 'entrepreneur'. usuarios y analisis ademas filtran por dueno con X-User-Id (lo fija el
# gateway); metodologias y beneficios son catalogos compartidos y solo exigen el rol.
PROTECT_LEGACY = True

# (metodo, ruta publica tras /api/v1/auth, ruta del micro, query strings, requiere JWT, timeout)
AUTH_OPERATIONS = [
    ("POST", "/register", "/auth/register", [], False, None),
    ("POST", "/login", "/auth/login", [], False, None),
    ("POST", "/refresh", "/auth/refresh", [], False, None),
    ("POST", "/logout", "/auth/logout", [], False, None),
    ("POST", "/password/forgot", "/auth/password/forgot", [], False, "15s"),
    ("POST", "/password/reset", "/auth/password/reset", [], False, None),
    ("GET", "/oauth/providers", "/auth/oauth/providers", [], False, None),
    ("GET", "/oauth/{provider}/login", "/auth/oauth/{provider}/login", ["role"], False, None),
    ("GET", "/oauth/{provider}/callback", "/auth/oauth/{provider}/callback", ["code", "state", "error"], False, "20s"),
    ("GET", "/me", "/auth/me", [], True, None),
    ("GET", "/me/audits", "/auth/me/audits", [], True, None),
    ("POST", "/roles", "/auth/roles", [], True, None),
]


# (metodo, ruta publica tras /api/v1, ruta del micro, query strings, acceso)
# acceso: "public" sin token | "user" cualquier rol | "owner" solo rol entrepreneur
# Las rutas de la cuenta viven bajo /me/... para no mezclar rutas fijas y con parametro
# bajo un mismo prefijo (/ventures/me vs /ventures/{id} puede chocar en el router del gateway).
VENTURE_OPERATIONS = [
    ("GET", "/categories", "/categories", [], "public"),
    ("GET", "/ventures", "/ventures", ["q", "category_id", "limit", "offset"], "public"),
    ("GET", "/ventures/{id}", "/ventures/{id}", [], "public"),
    ("GET", "/me/venture", "/me/venture", [], "owner"),
    ("PUT", "/me/venture", "/me/venture", [], "owner"),
    ("DELETE", "/me/venture", "/me/venture", [], "owner"),
    ("POST", "/me/venture/restore", "/me/venture/restore", [], "owner"),
    ("POST", "/me/venture/publish", "/me/venture/publish", [], "owner"),
    ("POST", "/me/venture/unpublish", "/me/venture/unpublish", [], "owner"),
    ("GET", "/me/venture/audits", "/me/venture/audits", [], "owner"),
    ("GET", "/me/venture/stats", "/me/venture/stats", [], "owner"),
    ("GET", "/me/venture/integrations", "/me/venture/integrations", [], "owner"),
    ("PUT", "/me/venture/image", "/me/venture/image", [], "owner"),
    ("DELETE", "/me/venture/image", "/me/venture/image", [], "owner"),
    ("GET", "/me/venture/youtube/start", "/me/venture/youtube/start", [], "owner"),
    # Google vuelve aqui SIN token: es publico, pero el micro solo acepta un `state` firmado por el
    ("GET", "/youtube/callback", "/youtube/callback", ["code", "state", "error", "scope"], "public"),
    ("PUT", "/me/venture/social/{platform}", "/me/venture/social/{platform}", [], "owner"),
    ("DELETE", "/me/venture/social/{platform}", "/me/venture/social/{platform}", [], "owner"),
    ("GET", "/me/favorites", "/me/favorites", [], "user"),
    ("GET", "/me/favorite-ids", "/me/favorite-ids", [], "user"),
    ("PUT", "/me/favorites/{id}", "/me/favorites/{id}", [], "user"),
    ("DELETE", "/me/favorites/{id}", "/me/favorites/{id}", [], "user"),
]


def jwt_validator(jwks_url, roles=None, propagate=False):
    cfg = {
        "auth/validator": {
            "alg": "RS256",
            "jwk_url": jwks_url,
            "cache": True,
            "cache_duration": 900,
            "disable_jwk_security": True,  # el JWKS se descarga por HTTP dentro de la red interna
            "issuer": JWT_ISSUER,
            "audience": [JWT_AUDIENCE],
            "roles_key": "roles",
            "roles": roles or ROLES,
        }
    }
    if propagate:
        # El micro recibe el id de la cuenta ya validado en X-User-Id. Solo se
        # declara en endpoints protegidos: el gateway lo SOBREESCRIBE con el del token.
        cfg["auth/validator"]["propagate_claims"] = [["sub", "X-User-Id"]]
    return cfg


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


def endpoint(method, public, backend_path, host, query, timeout=None, extra_headers=(), extra_config=None):
    ep = {
        "endpoint": public,
        "method": method,
        "output_encoding": "no-op",  # pasa tal cual codigo, cuerpo y errores del micro
        "input_query_strings": query if method == "GET" else [],
        # Content-Type es obligatorio para que el micro entienda JSON o multipart
        "input_headers": ["Content-Type", "Accept", *extra_headers],
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
    if extra_config:
        ep["extra_config"] = extra_config
    return ep


def build(hosts, jwks_url):
    endpoints = []
    for name, (public, prefix, _port, query) in SERVICES.items():
        host = hosts[name]
        for method, pub_suffix, back_suffix, _, _ in OPERATIONS:
            pub = f"/api/v1/{public}{pub_suffix}"
            back = f"{prefix}{back_suffix}"
            timeout = UPLOAD_TIMEOUT if (name == "usuarios" and method in ("POST", "PUT") and pub_suffix == "") else None
            if PROTECT_LEGACY:
                endpoints.append(
                    endpoint(method, pub, back, host, query, timeout,
                             ("Authorization", "X-User-Id"), jwt_validator(jwks_url, ["entrepreneur"], propagate=True))
                )
            else:
                endpoints.append(endpoint(method, pub, back, host, query, timeout))
        if name == "usuarios":
            if PROTECT_LEGACY:
                endpoints.append(
                    endpoint("PUT", "/api/v1/users/{id}/image", "/users/{id}/image", host, [], UPLOAD_TIMEOUT,
                             ("Authorization", "X-User-Id"), jwt_validator(jwks_url, ["entrepreneur"], propagate=True))
                )
            else:
                endpoints.append(
                    endpoint("PUT", "/api/v1/users/{id}/image", "/users/{id}/image", host, [], UPLOAD_TIMEOUT)
                )
    # ---- autenticacion ----
    for method, suffix, back, query, protected, timeout in AUTH_OPERATIONS:
        # Cookie: el refresh token viaja en una cookie httpOnly. Authorization: JWT.
        headers = ("Cookie", "Authorization") if protected else ("Cookie",)
        endpoints.append(
            endpoint(
                method, f"/api/v1/auth{suffix}", back, hosts["auth"], query, timeout,
                headers, jwt_validator(jwks_url) if protected else None,
            )
        )
    # ---- emprendimientos ----
    for method, pub, back, query, access in VENTURE_OPERATIONS:
        # Los endpoints protegidos reciben el id de la cuenta en X-User-Id (lo pone el
        # gateway a partir del token; lo que mande el cliente se descarta).
        if access == "public":
            ep = endpoint(method, f"/api/v1{pub}", back, hosts["emprendimientos"], query)
        else:
            roles = ["entrepreneur"] if access == "owner" else ROLES
            ep = endpoint(
                method, f"/api/v1{pub}", back, hosts["emprendimientos"], query,
                UPLOAD_TIMEOUT if (method == "PUT" and pub == "/me/venture/image") else None,
                ("Authorization", "X-User-Id"), jwt_validator(jwks_url, roles, propagate=True),
            )
        endpoints.append(ep)
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
    docker_hosts["auth"] = f"http://auth:{AUTH_PORT}"
    docker_hosts["emprendimientos"] = f"http://emprendimientos:{VENTURES_PORT}"
    local_hosts = {n: f"http://127.0.0.1:{s[2]}" for n, s in SERVICES.items()}
    local_hosts["auth"] = f"http://127.0.0.1:{AUTH_PORT}"
    local_hosts["emprendimientos"] = f"http://127.0.0.1:{VENTURES_PORT}"
    for filename, hosts in (("krakend.json", docker_hosts), ("krakend.local.json", local_hosts)):
        cfg = build(hosts, hosts["auth"] + "/.well-known/jwks.json")
        (here / filename).write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
        print(f"{filename}: {len(cfg['endpoints'])} endpoints")
