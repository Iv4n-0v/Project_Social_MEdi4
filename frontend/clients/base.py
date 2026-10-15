"""Cliente HTTP base para hablar con los microservicios a traves del gateway.

Patron Adapter: el monolito no sabe de URLs ni de httpx, solo llama metodos
como `analysis_client.create(...)`. Si cambia el gateway, se cambia aqui.
"""
import os

import httpx

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://127.0.0.1:8080")
API_PREFIX = "/api/v1"
TIMEOUT = 10  # segundos (Render gratis tarda en "despertar")


class ServiceUnavailable(Exception):
    """El gateway o el microservicio no respondio."""


class ServiceError(Exception):
    """El microservicio respondio con un error (404, 422...)."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class BaseClient:
    resource = ""  # p. ej. "analysis"

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = f"{base_url or GATEWAY_URL}{API_PREFIX}/{self.resource}"

    def _request(self, method: str, path: str = "", **kwargs):
        # Sin barra final en la coleccion: KrakenD define "/api/v1/<recurso>"
        url = f"{self.base_url}{path}"
        try:
            response = httpx.request(method, url, timeout=TIMEOUT, **kwargs)
        except httpx.RequestError:
            raise ServiceUnavailable(f"Servicio de {self.resource} no disponible")
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", "Error en el servicio")
            except ValueError:
                detail = "Error en el servicio"
            if not isinstance(detail, str):  # los 422 de FastAPI traen una lista
                detail = "Datos invalidos"
            raise ServiceError(response.status_code, detail)
        return response.json()


def or_none(fn, *args, **kwargs):
    """Ejecuta una llamada al micro; si responde 404 devuelve None (no existe)."""
    try:
        return fn(*args, **kwargs)
    except ServiceError as e:
        if e.status_code == 404:
            return None
        raise
