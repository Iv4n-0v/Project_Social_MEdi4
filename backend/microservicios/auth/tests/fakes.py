"""Piezas falsas para probar el servicio sin base de datos ni red."""
import datetime

from models import Account, AccountAudit, AccountRole, OAuthIdentity
from repository import DuplicateEmail


class FakeRepo:
    """Misma interfaz que AccountRepository, en memoria."""

    def __init__(self) -> None:
        self.accounts, self.role_rows, self.identities = {}, set(), []
        self.refresh, self.resets, self.audit_rows = [], [], []
        self.commits = 0
        self._next = 1

    def commit(self):
        self.commits += 1

    def get_account(self, account_id):
        return self.accounts.get(account_id)

    def get_account_by_email(self, email):
        return next((a for a in self.accounts.values() if a.email == email), None)

    def add_account(self, account):
        if self.get_account_by_email(account.email):
            raise DuplicateEmail(account.email)
        account.id = self._next
        self._next += 1
        self.accounts[account.id] = account
        return account

    def roles(self, account_id):
        return sorted(r for (a, r) in self.role_rows if a == account_id)

    def add_role(self, account_id, role):
        self.role_rows.add((account_id, role))

    def find_identity(self, provider, provider_user_id):
        return next(
            (i for i in self.identities
             if i.provider == provider and i.provider_user_id == provider_user_id),
            None,
        )

    def add_identity(self, account_id, provider, provider_user_id):
        self.identities.append(
            OAuthIdentity(account_id=account_id, provider=provider, provider_user_id=provider_user_id)
        )

    def add_refresh(self, token):
        self.refresh.append(token)

    def get_refresh_by_hash(self, token_hash):
        return next((t for t in self.refresh if t.token_hash == token_hash), None)

    def revoke_all_refresh(self, account_id, now):
        for t in self.refresh:
            if t.account_id == account_id and t.revoked_at is None:
                t.revoked_at = now

    def add_reset(self, token):
        self.resets.append(token)

    def get_reset_by_hash(self, token_hash):
        return next((t for t in self.resets if t.token_hash == token_hash), None)

    def save(self, obj):
        pass  # los objetos ya viven en memoria

    def add_audit(self, account_id, action):
        self.audit_rows.append(AccountAudit(account_id=account_id, action=action))

    def audits(self, account_id):
        return [a for a in self.audit_rows if a.account_id == account_id]

    def actions(self, account_id):
        return [a.action for a in self.audits(account_id)]


class FakeMailer:
    def __init__(self):
        self.sent = []

    def send_password_reset(self, to_email, link):
        self.sent.append((to_email, link))


class FakeProvider:
    """Proveedor OAuth de mentira: devuelve el perfil que se le indique."""

    def __init__(self, name="google", configured=True, profile=None):
        self.name = name
        self._configured = configured
        self.profile = profile
        self.calls = []

    def configured(self):
        return self._configured

    def authorize_url(self, state, redirect_uri):
        return f"https://proveedor.test/auth?state={state}&redirect_uri={redirect_uri}"

    def fetch_profile(self, code, redirect_uri, http):
        self.calls.append(code)
        return self.profile


class Clock:
    def __init__(self):
        # Arranca en la hora real: PyJWT valida "exp" con el reloj real
        self.now = datetime.datetime.now(datetime.timezone.utc)

    def __call__(self):
        return self.now

    def advance(self, **kw):
        self.now += datetime.timedelta(**kw)
