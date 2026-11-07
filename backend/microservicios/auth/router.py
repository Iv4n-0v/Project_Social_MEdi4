"""Capa HTTP del servicio de autenticacion (el "controlador").

Solo traduce HTTP <-> casos de uso. Sin reglas de negocio ni SQL.

Sesion segura:
- access token (JWT, 15 min) -> en el cuerpo JSON; el frontend lo guarda en memoria.
- refresh token (opaco, 7 dias) -> cookie httpOnly: JavaScript no puede leerla,
  asi un XSS no puede robarla. Solo se envia a /api/v1/auth.
"""
import html
import os
import urllib.parse
from functools import lru_cache
from typing import Annotated, Optional

from fastapi import APIRouter, Cookie, Depends, Header, Query, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse

import oauth
import security
import tokens
from database import SessionDep
from mailer import Mailer, get_mailer
from repository import AccountRepository
from schemas import (
    AccountResponse,
    AuditResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    OAuthStartResponse,
    ProvidersResponse,
    RegisterRequest,
    ResetPasswordRequest,
    RoleRequest,
    SessionResponse,
)
from service import AuthError, AuthService, AuthSession, Settings

router = APIRouter(prefix="/auth", tags=["auth"])
well_known = APIRouter(tags=["jwks"])

REFRESH_COOKIE = "refresh_token"
NONCE_COOKIE = "oauth_nonce"
COOKIE_PATH = "/api/v1/auth"  # ruta PUBLICA (la del gateway), no la interna


# ---- piezas compartidas (una sola instancia por proceso) ----
@lru_cache
def get_keys() -> tokens.KeyManager:
    return tokens.load_key_manager()


@lru_cache
def get_throttle() -> security.LoginThrottle:
    return security.LoginThrottle()


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()


@lru_cache
def get_providers() -> dict:
    return oauth.get_providers()


def get_service(session: SessionDep) -> AuthService:
    return AuthService(
        AccountRepository(session),
        get_keys(),
        get_mailer(),
        get_throttle(),
        get_settings(),
        providers=get_providers(),
    )


ServiceDep = Annotated[AuthService, Depends(get_service)]


def current_account(
    service: ServiceDep, authorization: Annotated[Optional[str], Header()] = None
):
    """Exige 'Authorization: Bearer <token>' y devuelve la cuenta activa."""
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise tokens.InvalidToken("Falta el token de acceso")
    return service.account_from_access_token(token.strip())


AccountDep = Annotated[object, Depends(current_account)]


# ---- helpers de cookies y respuestas ----
def _secure() -> bool:
    return os.getenv("COOKIE_SECURE", "false").lower() == "true"


def _set_refresh_cookie(response: Response, value: str, days: int) -> None:
    response.set_cookie(
        REFRESH_COOKIE,
        value,
        max_age=days * 86400,
        httponly=True,
        secure=_secure(),
        samesite="lax",
        path=COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE, path=COOKIE_PATH)


def _account_dto(account, roles) -> AccountResponse:
    return AccountResponse(
        id=account.id,
        email=account.email,
        name=account.name,
        roles=list(roles),
        has_password=bool(account.password_hash),
        created_at=account.created_at,
    )


def _session_dto(s: AuthSession) -> SessionResponse:
    return SessionResponse(
        access_token=s.access_token,
        expires_in=s.expires_in,
        account=_account_dto(s.account, s.roles),
    )


def _respond(response: Response, s: AuthSession, settings: Settings) -> SessionResponse:
    if s.refresh_token:
        _set_refresh_cookie(response, s.refresh_token, settings.refresh_days)
    return _session_dto(s)


# ---- registro, sesion ----
@router.post("/register", response_model=SessionResponse, status_code=201)
def register(data: RegisterRequest, response: Response, service: ServiceDep):
    s = service.register(data.email, data.password, data.name, data.role)
    return _respond(response, s, service.settings)


@router.post("/login", response_model=SessionResponse)
def login(data: LoginRequest, response: Response, service: ServiceDep):
    s = service.login(data.email, data.password)
    return _respond(response, s, service.settings)


@router.post("/refresh", response_model=SessionResponse)
def refresh(
    response: Response,
    service: ServiceDep,
    refresh_token: Annotated[Optional[str], Cookie(alias=REFRESH_COOKIE)] = None,
):
    """Renueva el acceso con la cookie de sesion (y rota la cookie)."""
    try:
        s = service.refresh(refresh_token)
    except AuthError as exc:
        # Una cookie invalida se borra del navegador (por eso no se usa raise)
        failed = JSONResponse(
            status_code=401,
            content={"detail": str(exc)},
            headers={"WWW-Authenticate": "Bearer"},
        )
        _clear_refresh_cookie(failed)
        return failed
    return _respond(response, s, service.settings)


@router.post("/logout", status_code=204)
def logout(
    service: ServiceDep,
    refresh_token: Annotated[Optional[str], Cookie(alias=REFRESH_COOKIE)] = None,
):
    service.logout(refresh_token)
    done = Response(status_code=204)
    _clear_refresh_cookie(done)
    return done


# ---- cuenta y roles (requieren token) ----
@router.get("/me", response_model=AccountResponse)
def me(account: AccountDep, service: ServiceDep):
    acc, roles = service.me(account)
    return _account_dto(acc, roles)


@router.post("/roles", response_model=SessionResponse)
def enable_role(data: RoleRequest, account: AccountDep, service: ServiceDep):
    """Habilita el otro rol en la misma cuenta y devuelve un token al dia."""
    return _session_dto(service.add_role(account, data.role))


@router.get("/me/audits", response_model=list[AuditResponse])
def my_audits(account: AccountDep, service: ServiceDep):
    return [
        AuditResponse(id=a.id, action=a.action, timestamp=a.timestamp)
        for a in service.audits(account)
    ]


# ---- recuperacion de contrasena ----
@router.post("/password/forgot", response_model=MessageResponse, status_code=202)
def forgot_password(data: ForgotPasswordRequest, service: ServiceDep):
    service.forgot_password(data.email)
    return MessageResponse(
        detail="Si el correo esta registrado, recibiras un enlace para restablecer la contrasena"
    )


@router.post("/password/reset", response_model=MessageResponse)
def reset_password(data: ResetPasswordRequest, service: ServiceDep):
    service.reset_password(data.token, data.new_password)
    return MessageResponse(detail="Contrasena actualizada. Inicia sesion de nuevo")


# ---- Google / Facebook ----
@router.get("/oauth/providers", response_model=ProvidersResponse)
def oauth_providers(service: ServiceDep):
    """Que proveedores estan configurados (el frontend solo muestra esos botones)."""
    status = service.providers_status()
    return ProvidersResponse(google=status.get("google", False), facebook=status.get("facebook", False))


@router.get("/oauth/{provider}/login", response_model=OAuthStartResponse)
def oauth_login(
    provider: str,
    response: Response,
    service: ServiceDep,
    role: str = Query("visitor"),
):
    """Devuelve la URL del proveedor; el frontend navega a ella.

    Se devuelve JSON (no una redireccion) para que atraviese bien el gateway.
    """
    url, nonce = service.oauth_start(provider, role)
    response.set_cookie(
        NONCE_COOKIE,
        nonce,
        max_age=600,
        httponly=True,
        secure=_secure(),
        samesite="lax",
        path=COOKIE_PATH,
    )
    return OAuthStartResponse(url=url)


def _bridge_page(target: str) -> str:
    safe = html.escape(target, quote=True)
    return (
        "<!doctype html><html lang='es'><head><meta charset='utf-8'>"
        f"<meta http-equiv='refresh' content='0;url={safe}'>"
        "<title>Redirigiendo...</title></head><body>"
        f"<p>Redirigiendo... <a href='{safe}'>Continuar</a></p></body></html>"
    )


@router.get("/oauth/{provider}/callback", response_class=HTMLResponse)
def oauth_callback(
    provider: str,
    service: ServiceDep,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    oauth_nonce: Annotated[Optional[str], Cookie(alias=NONCE_COOKIE)] = None,
):
    """Destino al que el proveedor devuelve al usuario.

    Responde con una pagina HTML que fija la cookie de sesion y lleva al
    frontend (sin redireccion 3xx, para que pase igual por el gateway).
    """
    s = service.settings
    try:
        if error or not code or not state:
            raise oauth.OAuthFailed("Se cancelo el inicio de sesion")
        session = service.oauth_finish(provider, code, state, oauth_nonce)
    except (AuthError, oauth.OAuthFailed, tokens.InvalidToken) as exc:
        target = f"{s.frontend_url}/ingresar?oauth_error=" + urllib.parse.quote(str(exc))
        page = HTMLResponse(_bridge_page(target))
        page.delete_cookie(NONCE_COOKIE, path=COOKIE_PATH)
        return page
    page = HTMLResponse(_bridge_page(f"{s.frontend_url}/?oauth=ok"))
    _set_refresh_cookie(page, session.refresh_token, s.refresh_days)
    page.delete_cookie(NONCE_COOKIE, path=COOKIE_PATH)
    return page


# ---- llave publica para el gateway ----
@well_known.get("/.well-known/jwks.json")
def jwks():
    """KrakenD descarga de aqui la llave publica para validar los JWT."""
    return get_keys().jwks()
