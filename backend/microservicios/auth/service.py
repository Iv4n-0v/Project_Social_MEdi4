"""Logica de negocio del servicio de autenticacion.

Responsabilidades (principio S): reglas de cuentas, roles, sesiones,
recuperacion de contrasena e inicio de sesion externo. No conoce HTTP (los
errores son clases con nombre propio; main.py las traduce a codigos) ni SQL
(eso es del repositorio).
"""
import datetime
import hmac
import logging
import os
import secrets
from dataclasses import dataclass
from typing import Optional

import oauth
import security
import tokens
from mailer import Mailer
from models import (
    ROLES,
    Account,
    PasswordResetToken,
    RefreshToken,
)
from oauth import HttpJson, OAuthFailed
from repository import DuplicateEmail

logger = logging.getLogger("auth.service")

OAUTH_STATE_MINUTES = 10


# ---- errores de dominio ----
class AuthError(Exception):
    """Base de todos los errores del servicio."""


class InvalidInput(AuthError):
    pass


class EmailAlreadyRegistered(AuthError):
    pass


class InvalidCredentials(AuthError):
    pass


class TooManyAttempts(AuthError):
    pass


class AccountDisabled(AuthError):
    pass


class AccountNotFound(AuthError):
    pass


REFRESH_GRACE_SECONDS = 10


class InvalidRefreshToken(AuthError):
    pass


class RefreshRaceLost(InvalidRefreshToken):
    """Dos pestañas renovaron a la vez: la otra ya roto el token.

    No es un robo. No se cierran sesiones ni se borra la cookie (que ya es la nueva).
    """


class InvalidResetToken(AuthError):
    pass


class ProviderNotFound(AuthError):
    pass


class ProviderNotConfigured(AuthError):
    pass


class OAuthEmailConflict(AuthError):
    pass


@dataclass
class Settings:
    public_url: str
    frontend_url: str
    refresh_days: int = 7
    reset_minutes: int = 60

    @classmethod
    def from_env(cls) -> "Settings":
        public = os.getenv("PUBLIC_URL", "http://localhost:8000").rstrip("/")
        return cls(
            public_url=public,
            frontend_url=os.getenv("FRONTEND_URL", public).rstrip("/"),
            refresh_days=int(os.getenv("REFRESH_TOKEN_DAYS", "7")),
            reset_minutes=int(os.getenv("RESET_TOKEN_MINUTES", "60")),
        )


@dataclass
class AuthSession:
    access_token: str
    expires_in: int
    account: Account
    roles: list
    refresh_token: Optional[str] = None  # None cuando solo se renueva el acceso


def _aware(value: datetime.datetime) -> datetime.datetime:
    """SQLite devuelve fechas sin zona horaria; se asume UTC."""
    return value if value.tzinfo else value.replace(tzinfo=datetime.timezone.utc)


class AuthService:
    def __init__(
        self,
        repo,
        keys: tokens.KeyManager,
        mailer: Mailer,
        throttle: security.LoginThrottle,
        settings: Settings,
        providers: Optional[dict] = None,
        http: HttpJson = oauth.urllib_json,
        clock=None,
    ) -> None:
        self.repo = repo
        self.keys = keys
        self.mailer = mailer
        self.throttle = throttle
        self.settings = settings
        self.providers = providers if providers is not None else oauth.get_providers()
        self.http = http
        self._clock = clock

    # ---- helpers ----
    def _now(self) -> datetime.datetime:
        return self._clock() if self._clock else datetime.datetime.now(datetime.timezone.utc)

    def _validate_role(self, role: str) -> str:
        if role not in ROLES:
            raise InvalidInput(f"Rol no valido. Opciones: {', '.join(ROLES)}")
        return role

    def _access_for(self, account: Account) -> tuple[str, list]:
        roles = self.repo.roles(account.id)
        token = self.keys.sign(tokens.access_claims(account.id, account.email, roles))
        return token, roles

    def _issue(self, account: Account) -> AuthSession:
        """Crea una sesion nueva: token de acceso + refresh token."""
        access, roles = self._access_for(account)
        refresh = security.new_opaque_token()
        self.repo.add_refresh(
            RefreshToken(
                account_id=account.id,
                token_hash=security.hash_token(refresh),
                expires_at=self._now() + datetime.timedelta(days=self.settings.refresh_days),
            )
        )
        return AuthSession(
            access_token=access,
            expires_in=tokens.ACCESS_MINUTES * 60,
            account=account,
            roles=roles,
            refresh_token=refresh,
        )

    def _active_account(self, account_id: int) -> Account:
        account = self.repo.get_account(account_id)
        if account is None:
            raise AccountNotFound("Cuenta no encontrada")
        if not account.is_active:
            raise AccountDisabled("La cuenta esta desactivada")
        return account

    def _create_account(self, email: str, name: str, password_hash, role: str) -> Account:
        try:
            account = self.repo.add_account(
                Account(email=email, name=name, password_hash=password_hash)
            )
        except DuplicateEmail as exc:
            raise EmailAlreadyRegistered("Ya existe una cuenta con ese correo") from exc
        self.repo.add_role(account.id, role)
        return account

    # ---- registro y sesion ----
    def register(self, email: str, password: str, name: str, role: str) -> AuthSession:
        email = security.normalize_email(email)
        if not security.is_valid_email(email):
            raise InvalidInput("Correo no valido")
        problem = security.password_problem(password)
        if problem:
            raise InvalidInput(problem)
        name = (name or "").strip()
        if not name:
            raise InvalidInput("El nombre es obligatorio")
        role = self._validate_role(role)
        if self.repo.get_account_by_email(email):
            raise EmailAlreadyRegistered("Ya existe una cuenta con ese correo")
        account = self._create_account(email, name, security.hash_password(password), role)
        self.repo.add_audit(account.id, "REGISTER")
        session = self._issue(account)
        self.repo.commit()
        return session

    def login(self, email: str, password: str) -> AuthSession:
        email = security.normalize_email(email)
        if self.throttle.blocked(email):
            raise TooManyAttempts("Demasiados intentos. Intenta de nuevo mas tarde")
        account = self.repo.get_account_by_email(email)
        if account is None or not account.password_hash:
            # correo inexistente o cuenta solo-Google/Facebook: se gasta el mismo
            # tiempo para no revelar que la cuenta existe
            security.verify_password(password, security.DUMMY_HASH)
            ok = False
        else:
            ok = security.verify_password(password, account.password_hash)
        if not ok:
            self.throttle.record_failure(email)
            if account is not None:
                self.repo.add_audit(account.id, "LOGIN_FAILED")
                self.repo.commit()
            raise InvalidCredentials("Correo o contrasena incorrectos")
        if not account.is_active:
            raise AccountDisabled("La cuenta esta desactivada")
        self.throttle.clear(email)
        self.repo.add_audit(account.id, "LOGIN")
        session = self._issue(account)
        self.repo.commit()
        return session

    def refresh(self, refresh_token: Optional[str]) -> AuthSession:
        """Rota el refresh token: el viejo se revoca y se entrega uno nuevo.

        Si llega un token YA revocado, alguien lo esta reutilizando (posible
        robo): se cierran todas las sesiones de esa cuenta.
        """
        if not refresh_token:
            raise InvalidRefreshToken("No hay sesion")
        record = self.repo.get_refresh_by_hash(security.hash_token(refresh_token))
        if record is None:
            raise InvalidRefreshToken("Sesion no valida")
        now = self._now()
        if record.revoked_at is not None:
            # Ventana de gracia: una peticion paralela legitima (pestañas, recarga)
            # llega unos milisegundos despues de la rotacion.
            if (now - _aware(record.revoked_at)).total_seconds() <= REFRESH_GRACE_SECONDS:
                raise RefreshRaceLost("Sesion renovada en otra peticion")
            self.repo.revoke_all_refresh(record.account_id, now)
            self.repo.add_audit(record.account_id, "REFRESH_REUSE_DETECTED")
            self.repo.commit()
            raise InvalidRefreshToken("Sesion no valida")
        if _aware(record.expires_at) <= now:
            raise InvalidRefreshToken("La sesion expiro")
        account = self.repo.get_account(record.account_id)
        if account is None or not account.is_active:
            raise InvalidRefreshToken("Sesion no valida")
        record.revoked_at = now
        self.repo.save(record)
        session = self._issue(account)
        self.repo.commit()
        return session

    def logout(self, refresh_token: Optional[str]) -> None:
        if not refresh_token:
            return
        record = self.repo.get_refresh_by_hash(security.hash_token(refresh_token))
        if record is not None and record.revoked_at is None:
            record.revoked_at = self._now()
            self.repo.save(record)
            self.repo.add_audit(record.account_id, "LOGOUT")
            self.repo.commit()

    # ---- cuenta y roles ----
    def account_from_access_token(self, access_token: str) -> Account:
        """Valida el JWT (firma, expiracion, emisor) y devuelve la cuenta activa."""
        claims = self.keys.verify(access_token)  # lanza tokens.InvalidToken
        try:
            account_id = int(claims["sub"])
        except (KeyError, ValueError) as exc:
            raise tokens.InvalidToken("Token sin identidad") from exc
        return self._active_account(account_id)

    def me(self, account: Account) -> tuple[Account, list]:
        return account, self.repo.roles(account.id)

    def add_role(self, account: Account, role: str) -> AuthSession:
        """Habilita el segundo rol en la misma cuenta (sin crear otra)."""
        role = self._validate_role(role)
        if role not in self.repo.roles(account.id):
            self.repo.add_role(account.id, role)
            self.repo.add_audit(account.id, f"ROLE_ADDED:{role}")
        access, roles = self._access_for(account)  # token nuevo con los roles al dia
        self.repo.commit()
        return AuthSession(
            access_token=access,
            expires_in=tokens.ACCESS_MINUTES * 60,
            account=account,
            roles=roles,
        )

    def audits(self, account: Account) -> list:
        return self.repo.audits(account.id)

    # ---- recuperacion de contrasena ----
    def forgot_password(self, email: str) -> None:
        """Siempre responde igual, exista o no el correo (no revela cuentas)."""
        email = security.normalize_email(email)
        account = self.repo.get_account_by_email(email) if email else None
        if account is None or not account.is_active:
            return
        raw = security.new_opaque_token()
        self.repo.add_reset(
            PasswordResetToken(
                account_id=account.id,
                token_hash=security.hash_token(raw),
                expires_at=self._now() + datetime.timedelta(minutes=self.settings.reset_minutes),
            )
        )
        self.repo.add_audit(account.id, "PASSWORD_RESET_REQUESTED")
        self.repo.commit()
        link = f"{self.settings.frontend_url}/restablecer?token={raw}"
        try:
            self.mailer.send_password_reset(account.email, link)
        except Exception:  # un fallo de correo no debe revelar si la cuenta existe
            logger.exception("No se pudo enviar el correo de recuperacion")

    def reset_password(self, token: str, new_password: str) -> None:
        problem = security.password_problem(new_password)
        if problem:
            raise InvalidInput(problem)
        record = self.repo.get_reset_by_hash(security.hash_token(token or ""))
        now = self._now()
        if record is None or record.used_at is not None or _aware(record.expires_at) <= now:
            raise InvalidResetToken("El enlace no es valido o ya expiro")
        account = self.repo.get_account(record.account_id)
        if account is None or not account.is_active:
            raise InvalidResetToken("El enlace no es valido o ya expiro")
        account.password_hash = security.hash_password(new_password)
        self.repo.save(account)
        record.used_at = now
        self.repo.save(record)
        self.repo.revoke_all_refresh(account.id, now)  # cierra sesiones abiertas
        self.repo.add_audit(account.id, "PASSWORD_RESET")
        self.throttle.clear(account.email)
        self.repo.commit()

    # ---- Google / Facebook ----
    def providers_status(self) -> dict:
        return {name: p.configured() for name, p in self.providers.items()}

    def _provider(self, name: str):
        provider = self.providers.get(name)
        if provider is None:
            raise ProviderNotFound("Proveedor desconocido")
        if not provider.configured():
            raise ProviderNotConfigured(
                f"El inicio de sesion con {name} no esta configurado en este servidor"
            )
        return provider

    def _redirect_uri(self, provider_name: str) -> str:
        return f"{self.settings.public_url}/api/v1/auth/oauth/{provider_name}/callback"

    def oauth_start(self, provider_name: str, role: str) -> tuple[str, str]:
        provider = self._provider(provider_name)
        role = self._validate_role(role)
        nonce = secrets.token_urlsafe(16)
        now = self._now()
        state = self.keys.sign(
            {
                "typ": "oauth_state",
                "provider": provider_name,
                "role": role,
                "nonce": nonce,
                "iss": tokens.ISSUER,
                "aud": tokens.STATE_AUDIENCE,
                "iat": now,
                "exp": now + datetime.timedelta(minutes=OAUTH_STATE_MINUTES),
            }
        )
        return provider.authorize_url(state, self._redirect_uri(provider_name)), nonce

    def oauth_finish(self, provider_name: str, code: str, state: str, nonce: Optional[str]) -> AuthSession:
        provider = self._provider(provider_name)
        try:
            claims = self.keys.verify(state, audience=tokens.STATE_AUDIENCE)
        except tokens.InvalidToken as exc:
            raise OAuthFailed("La solicitud de inicio de sesion expiro o no es valida") from exc
        if (
            claims.get("typ") != "oauth_state"
            or claims.get("provider") != provider_name
            or not nonce
            or not hmac.compare_digest(str(claims.get("nonce", "")), nonce)
        ):
            raise OAuthFailed("La solicitud de inicio de sesion no es valida")
        if not code:
            raise OAuthFailed("El proveedor no entrego un codigo")

        profile = provider.fetch_profile(code, self._redirect_uri(provider_name), self.http)

        identity = self.repo.find_identity(provider_name, profile.subject)
        if identity is not None:
            account = self._active_account(identity.account_id)
            action = "LOGIN_OAUTH"
        else:
            if not profile.email:
                raise OAuthFailed(
                    "El proveedor no entrego un correo; registrate con correo y contrasena"
                )
            email = security.normalize_email(profile.email)
            if not security.is_valid_email(email):
                raise OAuthFailed("El proveedor entrego un correo no valido")
            # Nunca se enlaza automaticamente con una cuenta existente: como el
            # registro con contrasena no verifica el correo, enlazar permitiria
            # que alguien se adelante a la victima. Se pide ingresar con la contrasena.
            if self.repo.get_account_by_email(email):
                raise OAuthEmailConflict(
                    "Ya existe una cuenta con ese correo. Ingresa con tu contrasena "
                    "o usa la recuperacion de contrasena"
                )
            name = (profile.name or email.split("@")[0]).strip()[:100] or "Usuario"
            account = self._create_account(email, name, None, claims["role"])
            self.repo.add_identity(account.id, provider_name, profile.subject)
            self.repo.add_audit(account.id, f"REGISTER_OAUTH:{provider_name}")
            action = "LOGIN_OAUTH"
        self.repo.add_audit(account.id, action)
        session = self._issue(account)
        self.repo.commit()
        return session
