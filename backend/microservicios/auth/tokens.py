"""Tokens de acceso JWT firmados con RS256.

La llave PRIVADA solo la tiene este servicio. El gateway (KrakenD) descarga la
llave PUBLICA en /.well-known/jwks.json y valida cada token sin llamar aqui.
Asi no hay secretos compartidos entre servicios.

Reclamos (claims): sub (id de la cuenta), email, roles (lista), iss, aud, iat,
exp, jti. Dura poco (15 min); la sesion larga la da el refresh token.
"""
import base64
import datetime
import hashlib
import os
import uuid
from pathlib import Path

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

ALGORITHM = "RS256"
ISSUER = os.getenv("JWT_ISSUER", "social-media-auth")
AUDIENCE = os.getenv("JWT_AUDIENCE", "social-media-api")
ACCESS_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "15"))
# El "state" de OAuth usa OTRA audiencia: nunca sirve como token de acceso
STATE_AUDIENCE = "social-media-oauth-state"


class InvalidToken(Exception):
    pass


def _b64url_uint(value: int) -> str:
    raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


class KeyManager:
    """Carga o crea la llave privada y expone la publica en formato JWKS."""

    def __init__(self, private_pem: bytes | None = None) -> None:
        self._private = (
            serialization.load_pem_private_key(private_pem, password=None)
            if private_pem
            else rsa.generate_private_key(public_exponent=65537, key_size=2048)
        )
        numbers = self._private.public_key().public_numbers()
        self.kid = hashlib.sha256(
            (str(numbers.n) + ":" + str(numbers.e)).encode()
        ).hexdigest()[:16]
        self._jwk = {
            "kty": "RSA",
            "use": "sig",
            "alg": ALGORITHM,
            "kid": self.kid,
            "n": _b64url_uint(numbers.n),
            "e": _b64url_uint(numbers.e),
        }

    def private_pem(self) -> bytes:
        return self._private.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )

    def jwks(self) -> dict:
        return {"keys": [self._jwk]}

    def sign(self, claims: dict) -> str:
        return jwt.encode(
            claims, self._private, algorithm=ALGORITHM, headers={"kid": self.kid}
        )

    def verify(self, token: str, audience: str = AUDIENCE) -> dict:
        try:
            return jwt.decode(
                token,
                self._private.public_key(),
                algorithms=[ALGORITHM],
                audience=audience,
                issuer=ISSUER,
            )
        except jwt.PyJWTError as exc:
            raise InvalidToken(str(exc)) from exc


def load_key_manager() -> KeyManager:
    """Prioridad: variable JWT_PRIVATE_KEY (PEM) > archivo JWT_KEY_FILE > crear.

    Si se crea, se guarda en JWT_KEY_FILE (por defecto /data/jwt_private.pem,
    montado como volumen) para que los tokens sigan validos al reiniciar.
    """
    pem_env = os.getenv("JWT_PRIVATE_KEY")
    if pem_env:
        return KeyManager(pem_env.replace("\\n", "\n").encode())
    path = Path(os.getenv("JWT_KEY_FILE", "/data/jwt_private.pem"))
    try:
        if path.exists():
            return KeyManager(path.read_bytes())
        manager = KeyManager()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(manager.private_pem())
        path.chmod(0o600)
        return manager
    except OSError:
        # Sin disco escribible: llave temporal (los tokens mueren al reiniciar)
        return KeyManager()


def access_claims(account_id: int, email: str, roles: list[str]) -> dict:
    now = datetime.datetime.now(datetime.timezone.utc)
    return {
        "sub": str(account_id),
        "email": email,
        "roles": sorted(roles),
        "iss": ISSUER,
        "aud": [AUDIENCE],
        "iat": now,
        "exp": now + datetime.timedelta(minutes=ACCESS_MINUTES),
        "jti": uuid.uuid4().hex,
    }
