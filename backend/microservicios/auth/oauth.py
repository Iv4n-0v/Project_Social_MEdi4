"""Inicio de sesion con Google y Facebook (OAuth 2.0, flujo de codigo).

Solo AUTENTICA (quien eres). No pide permisos de redes del negocio.
Si faltan las credenciales en el entorno, el proveedor aparece como no
configurado y el boton correspondiente no debe mostrarse: nunca se simula un
inicio de sesion.

Las llamadas HTTP salen por la funcion `http_json` (por defecto urllib) para
poder probar sin red.
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Callable, Optional


class OAuthFailed(Exception):
    """El proveedor respondio con error o con datos inesperados."""


@dataclass
class OAuthProfile:
    provider: str
    subject: str  # id del usuario en el proveedor (estable)
    email: Optional[str]
    email_verified: bool
    name: Optional[str]


# (metodo, url, datos de formulario o None, cabeceras o None) -> JSON
HttpJson = Callable[[str, str, Optional[dict], Optional[dict]], dict]


def urllib_json(method: str, url: str, data: Optional[dict], headers: Optional[dict]) -> dict:
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, ValueError, TimeoutError) as exc:
        raise OAuthFailed("No se pudo hablar con el proveedor") from exc


class GoogleProvider:
    name = "google"

    def __init__(self) -> None:
        self.client_id = os.getenv("GOOGLE_CLIENT_ID", "")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")

    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def authorize_url(self, state: str, redirect_uri: str) -> str:
        q = urllib.parse.urlencode(
            {
                "client_id": self.client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
                "prompt": "select_account",
            }
        )
        return f"https://accounts.google.com/o/oauth2/v2/auth?{q}"

    def fetch_profile(self, code: str, redirect_uri: str, http: HttpJson) -> OAuthProfile:
        token = http(
            "POST",
            "https://oauth2.googleapis.com/token",
            {
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            None,
        )
        access = token.get("access_token")
        if not access:
            raise OAuthFailed("Google no entrego un token de acceso")
        info = http(
            "GET",
            "https://openidconnect.googleapis.com/v1/userinfo",
            None,
            {"Authorization": f"Bearer {access}"},
        )
        if not info.get("sub"):
            raise OAuthFailed("Google no entrego la identidad del usuario")
        return OAuthProfile(
            provider=self.name,
            subject=str(info["sub"]),
            email=(info.get("email") or None),
            email_verified=bool(info.get("email_verified")),
            name=info.get("name"),
        )


class FacebookProvider:
    name = "facebook"

    def __init__(self) -> None:
        self.app_id = os.getenv("FACEBOOK_APP_ID", "")
        self.app_secret = os.getenv("FACEBOOK_APP_SECRET", "")
        # Ajustar a la version vigente en developers.facebook.com
        self.version = os.getenv("FACEBOOK_API_VERSION", "v23.0")

    def configured(self) -> bool:
        return bool(self.app_id and self.app_secret)

    def authorize_url(self, state: str, redirect_uri: str) -> str:
        q = urllib.parse.urlencode(
            {
                "client_id": self.app_id,
                "redirect_uri": redirect_uri,
                "state": state,
                "scope": "email,public_profile",
                "response_type": "code",
            }
        )
        return f"https://www.facebook.com/{self.version}/dialog/oauth?{q}"

    def fetch_profile(self, code: str, redirect_uri: str, http: HttpJson) -> OAuthProfile:
        q = urllib.parse.urlencode(
            {
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "redirect_uri": redirect_uri,
                "code": code,
            }
        )
        token = http(
            "GET", f"https://graph.facebook.com/{self.version}/oauth/access_token?{q}", None, None
        )
        access = token.get("access_token")
        if not access:
            raise OAuthFailed("Facebook no entrego un token de acceso")
        me = http(
            "GET",
            f"https://graph.facebook.com/{self.version}/me?"
            + urllib.parse.urlencode({"fields": "id,name,email", "access_token": access}),
            None,
            None,
        )
        if not me.get("id"):
            raise OAuthFailed("Facebook no entrego la identidad del usuario")
        # Facebook no indica si el correo esta verificado: nunca se usa para
        # enlazar con una cuenta existente (ver service.py).
        return OAuthProfile(
            provider=self.name,
            subject=str(me["id"]),
            email=(me.get("email") or None),
            email_verified=False,
            name=me.get("name"),
        )


def get_providers() -> dict:
    return {p.name: p for p in (GoogleProvider(), FacebookProvider())}
