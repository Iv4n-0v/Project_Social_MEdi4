"""Conexion oficial con YouTube (YouTube Data API v3) para leer los suscriptores.

Por que asi:
- Se usa `channels.list?mine=true` con el permiso de SOLO LECTURA `youtube.readonly`:
  el canal que responde es el de la cuenta de Google que inicio sesion, asi que el
  emprendedor demuestra que es el dueno (no basta pegar un enlace).
- El token de Google se usa una vez y se descarta: no se guarda ninguna credencial.
  Para refrescar la cifra, el emprendedor vuelve a pulsar el boton.
- Nada se simula: si el canal oculta sus suscriptores o la API falla, no se guarda cifra.
"""
import json
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Callable, Optional

import jwt

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"
SCOPE = "https://www.googleapis.com/auth/youtube.readonly"
STATE_AUDIENCE = "social-media-youtube-connect"
STATE_TTL_SECONDS = 600
CALLBACK_PATH = "/api/v1/youtube/callback"


class YoutubeError(Exception):
    code = "failed"  # codigo corto que viaja a la interfaz (nunca texto del usuario)


class NotConfigured(YoutubeError):
    code = "notconfigured"


class InvalidState(YoutubeError):
    code = "invalid"


class ExchangeFailed(YoutubeError):
    code = "failed"


class NoChannel(YoutubeError):
    code = "nochannel"


@dataclass(frozen=True)
class ChannelInfo:
    channel_id: str
    title: str
    subscribers: Optional[int]  # None si el canal oculta la cifra
    hidden: bool


def _urllib_http(method: str, url: str, data: Optional[dict] = None, headers: Optional[dict] = None) -> dict:
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise ExchangeFailed("No se pudo contactar a Google") from exc


class YoutubeConnector:
    def __init__(
        self,
        client_id: str = "",
        client_secret: str = "",
        public_url: str = "",
        state_secret: str = "",
        http: Callable = _urllib_http,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.public_url = public_url.rstrip("/")
        # Sin secreto fijo se genera uno por proceso (vale para una sola replica)
        self._state_secret = state_secret or secrets.token_urlsafe(32)
        self._http = http
        self._clock = clock

    @classmethod
    def from_env(cls) -> "YoutubeConnector":
        return cls(
            client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
            public_url=os.getenv("PUBLIC_URL", ""),
            state_secret=os.getenv("OAUTH_STATE_SECRET", ""),
        )

    @property
    def enabled(self) -> bool:
        return bool(self.client_id and self.client_secret and self.public_url)

    @property
    def redirect_uri(self) -> str:
        return self.public_url + CALLBACK_PATH

    # ---- paso 1: enviar al emprendedor a Google ----
    def authorize_url(self, account_id: int) -> str:
        if not self.enabled:
            raise NotConfigured("La conexion con YouTube no esta configurada")
        now = int(self._clock())
        state = jwt.encode(
            {"sub": str(account_id), "aud": STATE_AUDIENCE, "iat": now, "exp": now + STATE_TTL_SECONDS},
            self._state_secret,
            algorithm="HS256",
        )
        query = urllib.parse.urlencode(
            {
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
                "response_type": "code",
                "scope": SCOPE,
                "state": state,
                "access_type": "online",  # sin refresh token: no guardamos credenciales
                "prompt": "select_account",  # que elija la cuenta de Google duena del canal
            }
        )
        return f"{AUTH_URL}?{query}"

    # ---- paso 2: Google vuelve con ?code&state ----
    def account_from_state(self, state: str) -> int:
        """El `state` firmado dice que cuenta inicio el flujo (el callback no trae sesion)."""
        try:
            claims = jwt.decode(
                state,
                self._state_secret,
                algorithms=["HS256"],
                audience=STATE_AUDIENCE,
                options={"require": ["exp", "sub", "aud"]},
                leeway=0,
            )
            return int(claims["sub"])
        except (jwt.PyJWTError, ValueError, TypeError) as exc:
            raise InvalidState("Estado invalido o vencido") from exc

    def exchange_code(self, code: str) -> str:
        data = self._http(
            "POST",
            TOKEN_URL,
            {
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
                "grant_type": "authorization_code",
            },
            {"Accept": "application/json"},
        )
        token = data.get("access_token") if isinstance(data, dict) else None
        if not token:
            raise ExchangeFailed("Google no entrego el permiso")
        return token

    def fetch_channel(self, access_token: str) -> ChannelInfo:
        query = urllib.parse.urlencode({"part": "snippet,statistics", "mine": "true"})
        data = self._http("GET", f"{CHANNELS_URL}?{query}", None, {"Authorization": f"Bearer {access_token}"})
        items = data.get("items") if isinstance(data, dict) else None
        if not items:
            raise NoChannel("Esa cuenta de Google no tiene un canal de YouTube")
        item = items[0]
        stats = item.get("statistics") or {}
        hidden = bool(stats.get("hiddenSubscriberCount"))
        subs = None
        if not hidden and "subscriberCount" in stats:
            try:
                subs = int(stats["subscriberCount"])
            except (TypeError, ValueError):
                subs = None
        channel_id = item.get("id")
        if not channel_id:
            raise ExchangeFailed("Respuesta de YouTube incompleta")
        return ChannelInfo(
            channel_id=channel_id,
            title=(item.get("snippet") or {}).get("title", ""),
            subscribers=subs,
            hidden=subs is None,
        )


_connector = YoutubeConnector.from_env()


def get_connector() -> YoutubeConnector:
    """Dependencia de FastAPI. En pruebas se reemplaza con dependency_overrides."""
    return _connector
