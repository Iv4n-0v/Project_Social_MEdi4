"""Contrasenas y tokens opacos. Solo libreria estandar de Python.

- Contrasenas: scrypt (funcion de derivacion lenta, recomendada por OWASP),
  con sal aleatoria por contrasena. Nunca se guarda la contrasena en claro.
- Tokens opacos (refresh y recuperacion): se generan aleatorios y en la base de
  datos solo se guarda su SHA-256. Si la BD se filtra, los tokens no sirven.
"""
import base64
import hashlib
import hmac
import re
import secrets

# Parametros de scrypt (memoria ~16 MB por hash, cabe en el limite por defecto)
_N, _R, _P = 2**14, 8, 1
_SCHEME = "scrypt"

MIN_PASSWORD = 8
MAX_PASSWORD = 128
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def is_valid_email(email: str) -> bool:
    return bool(email) and len(email) <= 254 and bool(_EMAIL_RE.match(email))


def password_problem(password: str) -> str | None:
    """Devuelve el motivo si la contrasena no sirve, o None si es valida."""
    if not isinstance(password, str) or len(password) < MIN_PASSWORD:
        return f"La contrasena debe tener al menos {MIN_PASSWORD} caracteres"
    if len(password) > MAX_PASSWORD:
        return f"La contrasena no puede superar {MAX_PASSWORD} caracteres"
    return None


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=_N, r=_R, p=_P, dklen=32
    )
    return f"{_SCHEME}${_N}${_R}${_P}${_b64(salt)}${_b64(digest)}"


def verify_password(password: str, stored: str | None) -> bool:
    """Compara en tiempo constante. Una cuenta sin contrasena nunca coincide."""
    if not stored:
        return False
    try:
        scheme, n, r, p, salt_b64, digest_b64 = stored.split("$")
        if scheme != _SCHEME:
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        candidate = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(candidate, expected)


# Hash de relleno: se verifica contra el cuando el correo no existe, para que
# "correo inexistente" y "contrasena incorrecta" tarden lo mismo.
DUMMY_HASH = hash_password("relleno-para-igualar-tiempos")


def new_opaque_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class LoginThrottle:
    """Frena la adivinanza de contrasenas: N fallos por correo en una ventana.

    Vive en memoria del proceso: con varias replicas cada una cuenta por su
    lado (limitacion conocida; para produccion se movera a Redis o a la BD).
    """

    def __init__(self, max_failures: int = 5, window_seconds: int = 900, clock=None) -> None:
        import time
        from collections import defaultdict, deque

        self.max_failures = max_failures
        self.window = window_seconds
        self._clock = clock or time.monotonic
        self._failures = defaultdict(deque)

    def _prune(self, key: str) -> None:
        q = self._failures[key]
        limit = self._clock() - self.window
        while q and q[0] < limit:
            q.popleft()

    def blocked(self, key: str) -> bool:
        self._prune(key)
        return len(self._failures[key]) >= self.max_failures

    def record_failure(self, key: str) -> None:
        self._failures[key].append(self._clock())

    def clear(self, key: str) -> None:
        self._failures.pop(key, None)
