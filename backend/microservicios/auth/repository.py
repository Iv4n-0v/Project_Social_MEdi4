"""Acceso a datos del servicio de autenticacion (patron Repository).

Es la unica capa que conoce SQL/SQLModel.
"""
import datetime
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from models import (
    Account,
    AccountAudit,
    AccountRole,
    OAuthIdentity,
    PasswordResetToken,
    RefreshToken,
)


class DuplicateEmail(Exception):
    """Otra cuenta ya usa ese correo (la BD lo impide con una restriccion unica)."""


class AccountRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def commit(self) -> None:
        self.session.commit()

    # ---- cuentas ----
    def get_account(self, account_id: int) -> Optional[Account]:
        return self.session.get(Account, account_id)

    def get_account_by_email(self, email: str) -> Optional[Account]:
        return self.session.exec(select(Account).where(Account.email == email)).first()

    def add_account(self, account: Account) -> Account:
        self.session.add(account)
        try:
            self.session.flush()  # asigna account.id sin cerrar la transaccion
        except IntegrityError as exc:
            self.session.rollback()
            raise DuplicateEmail(account.email) from exc
        return account

    # ---- roles ----
    def roles(self, account_id: int) -> list[str]:
        rows = self.session.exec(
            select(AccountRole.role)
            .where(AccountRole.account_id == account_id)
            .order_by(AccountRole.role)
        ).all()
        return list(rows)

    def add_role(self, account_id: int, role: str) -> None:
        if role not in self.roles(account_id):
            self.session.add(AccountRole(account_id=account_id, role=role))
            self.session.flush()

    # ---- identidades externas (Google / Facebook) ----
    def find_identity(self, provider: str, provider_user_id: str) -> Optional[OAuthIdentity]:
        return self.session.exec(
            select(OAuthIdentity)
            .where(OAuthIdentity.provider == provider)
            .where(OAuthIdentity.provider_user_id == provider_user_id)
        ).first()

    def add_identity(self, account_id: int, provider: str, provider_user_id: str) -> None:
        self.session.add(
            OAuthIdentity(
                account_id=account_id,
                provider=provider,
                provider_user_id=provider_user_id,
            )
        )
        self.session.flush()

    # ---- sesiones (refresh tokens) ----
    def add_refresh(self, token: RefreshToken) -> None:
        self.session.add(token)
        self.session.flush()

    def get_refresh_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        return self.session.exec(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        ).first()

    def revoke_all_refresh(self, account_id: int, now: datetime.datetime) -> None:
        rows = self.session.exec(
            select(RefreshToken)
            .where(RefreshToken.account_id == account_id)
            .where(RefreshToken.revoked_at == None)  # noqa: E711  (SQL IS NULL)
        ).all()
        for row in rows:
            row.revoked_at = now
            self.session.add(row)

    # ---- recuperacion de contrasena ----
    def add_reset(self, token: PasswordResetToken) -> None:
        self.session.add(token)
        self.session.flush()

    def get_reset_by_hash(self, token_hash: str) -> Optional[PasswordResetToken]:
        return self.session.exec(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        ).first()

    def save(self, obj) -> None:
        """Marca un objeto modificado para guardarlo en el commit."""
        self.session.add(obj)

    # ---- auditoria ----
    def add_audit(self, account_id: int, action: str) -> None:
        self.session.add(AccountAudit(account_id=account_id, action=action))

    def audits(self, account_id: int) -> list[AccountAudit]:
        return list(
            self.session.exec(
                select(AccountAudit)
                .where(AccountAudit.account_id == account_id)
                .order_by(AccountAudit.id)
            ).all()
        )
