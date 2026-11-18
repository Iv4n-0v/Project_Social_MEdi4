import re
import unittest
import urllib.parse

import oauth
import security
import service as svc
import tokens
from tests.fakes import Clock, FakeMailer, FakeProvider, FakeRepo

PWD = "Clave12345"


def make(providers=None):
    repo, mailer, clock = FakeRepo(), FakeMailer(), Clock()
    keys = tokens.KeyManager()
    s = svc.AuthService(
        repo, keys, mailer, security.LoginThrottle(clock=lambda: clock.now.timestamp()),
        svc.Settings(public_url="http://app.test", frontend_url="http://app.test"),
        providers=providers if providers is not None else {}, clock=clock,
    )
    return s, repo, mailer, clock, keys


class RegisterTests(unittest.TestCase):
    def test_register_creates_account_role_session_and_audit(self):
        s, repo, *_ = make()
        out = s.register("  Ana@Mail.com ", PWD, " Ana ", "entrepreneur")
        self.assertEqual(out.account.email, "ana@mail.com")
        self.assertEqual(out.account.name, "Ana")
        self.assertEqual(out.roles, ["entrepreneur"])
        self.assertTrue(out.refresh_token)
        self.assertNotEqual(out.account.password_hash, PWD)
        self.assertEqual(repo.actions(out.account.id), ["REGISTER"])
        self.assertEqual(s.keys.verify(out.access_token)["roles"], ["entrepreneur"])
        self.assertGreaterEqual(repo.commits, 1)

    def test_only_the_refresh_hash_is_stored(self):
        s, repo, *_ = make()
        out = s.register("a@b.co", PWD, "A", "visitor")
        self.assertNotEqual(repo.refresh[0].token_hash, out.refresh_token)
        self.assertEqual(repo.refresh[0].token_hash, security.hash_token(out.refresh_token))

    def test_duplicate_email_any_case(self):
        s, *_ = make()
        s.register("a@b.co", PWD, "A", "visitor")
        with self.assertRaises(svc.EmailAlreadyRegistered):
            s.register("A@B.CO", PWD, "Otra", "visitor")

    def test_validation(self):
        s, *_ = make()
        for args in (("malo", PWD, "A", "visitor"), ("a@b.co", "corta", "A", "visitor"),
                     ("a@b.co", PWD, "   ", "visitor"), ("a@b.co", PWD, "A", "admin")):
            with self.assertRaises(svc.InvalidInput, msg=str(args)):
                s.register(*args)


class LoginTests(unittest.TestCase):
    def setUp(self):
        self.s, self.repo, self.mailer, self.clock, self.keys = make()
        self.acc = self.s.register("a@b.co", PWD, "A", "visitor").account

    def test_login_ok(self):
        out = self.s.login("A@b.co", PWD)
        self.assertEqual(out.account.id, self.acc.id)
        self.assertIn("LOGIN", self.repo.actions(self.acc.id))

    def test_wrong_password_and_unknown_email_look_the_same(self):
        for email, pwd in (("a@b.co", "incorrecta1"), ("nadie@b.co", PWD)):
            with self.assertRaises(svc.InvalidCredentials) as cm:
                self.s.login(email, pwd)
            self.assertEqual(str(cm.exception), "Correo o contrasena incorrectos")
        self.assertIn("LOGIN_FAILED", self.repo.actions(self.acc.id))

    def test_throttle_blocks_even_the_right_password(self):
        for _ in range(5):
            with self.assertRaises(svc.InvalidCredentials):
                self.s.login("a@b.co", "incorrecta1")
        with self.assertRaises(svc.TooManyAttempts):
            self.s.login("a@b.co", PWD)
        self.clock.advance(minutes=16)
        self.assertTrue(self.s.login("a@b.co", PWD).access_token)

    def test_successful_login_resets_the_counter(self):
        for _ in range(4):
            with self.assertRaises(svc.InvalidCredentials):
                self.s.login("a@b.co", "incorrecta1")
        self.s.login("a@b.co", PWD)
        with self.assertRaises(svc.InvalidCredentials):  # sigue contando desde cero
            self.s.login("a@b.co", "incorrecta1")

    def test_disabled_account_cannot_login(self):
        self.acc.is_active = False
        with self.assertRaises(svc.AccountDisabled):
            self.s.login("a@b.co", PWD)

    def test_oauth_only_account_has_no_password_login(self):
        self.acc.password_hash = None
        with self.assertRaises(svc.InvalidCredentials):
            self.s.login("a@b.co", PWD)


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.s, self.repo, self.mailer, self.clock, self.keys = make()
        self.first = self.s.register("a@b.co", PWD, "A", "visitor")

    def test_refresh_rotates_the_token(self):
        second = self.s.refresh(self.first.refresh_token)
        self.assertNotEqual(second.refresh_token, self.first.refresh_token)
        with self.assertRaises(svc.InvalidRefreshToken):  # el viejo ya no sirve
            self.s.refresh(self.first.refresh_token)

    def test_reusing_a_revoked_token_closes_every_session(self):
        second = self.s.refresh(self.first.refresh_token)
        self.clock.advance(seconds=svc.REFRESH_GRACE_SECONDS + 1)  # fuera de la ventana de gracia
        with self.assertRaises(svc.InvalidRefreshToken):
            self.s.refresh(self.first.refresh_token)  # reuso = posible robo
        with self.assertRaises(svc.InvalidRefreshToken):
            self.s.refresh(second.refresh_token)  # el legitimo tambien cae
        self.assertIn("REFRESH_REUSE_DETECTED", self.repo.actions(self.first.account.id))

    def test_parallel_refresh_inside_grace_window_is_not_theft(self):
        second = self.s.refresh(self.first.refresh_token)
        with self.assertRaises(svc.RefreshRaceLost):
            self.s.refresh(self.first.refresh_token)  # la otra pestaña, milisegundos despues
        self.assertNotIn("REFRESH_REUSE_DETECTED", self.repo.actions(self.first.account.id))
        self.s.refresh(second.refresh_token)  # la sesion legitima sigue viva

    def test_missing_unknown_and_expired(self):
        for bad in (None, "", "inventado"):
            with self.assertRaises(svc.InvalidRefreshToken):
                self.s.refresh(bad)
        self.clock.advance(days=8)
        with self.assertRaises(svc.InvalidRefreshToken):
            self.s.refresh(self.first.refresh_token)

    def test_logout_revokes_and_is_idempotent(self):
        self.s.logout(self.first.refresh_token)
        self.s.logout(self.first.refresh_token)
        self.s.logout(None)
        with self.assertRaises(svc.InvalidRefreshToken):
            self.s.refresh(self.first.refresh_token)

    def test_refresh_of_disabled_account_fails(self):
        self.first.account.is_active = False
        with self.assertRaises(svc.InvalidRefreshToken):
            self.s.refresh(self.first.refresh_token)


class AccessTokenAndRolesTests(unittest.TestCase):
    def setUp(self):
        self.s, self.repo, self.mailer, self.clock, self.keys = make()
        self.out = self.s.register("a@b.co", PWD, "A", "visitor")

    def test_account_from_token(self):
        self.assertEqual(self.s.account_from_access_token(self.out.access_token).id, self.out.account.id)
        with self.assertRaises(tokens.InvalidToken):
            self.s.account_from_access_token("basura")

    def test_token_of_disabled_account_is_refused(self):
        self.out.account.is_active = False
        with self.assertRaises(svc.AccountDisabled):
            self.s.account_from_access_token(self.out.access_token)

    def test_enable_second_role_on_same_account(self):
        out = self.s.add_role(self.out.account, "entrepreneur")
        self.assertEqual(out.roles, ["entrepreneur", "visitor"])
        self.assertEqual(self.s.keys.verify(out.access_token)["roles"], ["entrepreneur", "visitor"])
        self.assertIsNone(out.refresh_token)
        self.assertEqual(len(self.repo.accounts), 1)  # no se creo otra cuenta
        self.s.add_role(self.out.account, "entrepreneur")  # idempotente
        self.assertEqual(self.repo.roles(self.out.account.id), ["entrepreneur", "visitor"])
        self.assertEqual(self.repo.actions(self.out.account.id).count("ROLE_ADDED:entrepreneur"), 1)

    def test_invalid_role(self):
        with self.assertRaises(svc.InvalidInput):
            self.s.add_role(self.out.account, "superadmin")


class PasswordResetTests(unittest.TestCase):
    def setUp(self):
        self.s, self.repo, self.mailer, self.clock, self.keys = make()
        self.out = self.s.register("a@b.co", PWD, "A", "visitor")

    def _token(self):
        link = self.mailer.sent[-1][1]
        self.assertTrue(link.startswith("http://app.test/restablecer?token="))
        return link.split("token=")[1]

    def test_unknown_email_sends_nothing_and_does_not_fail(self):
        self.s.forgot_password("nadie@b.co")
        self.s.forgot_password("")
        self.assertEqual(self.mailer.sent, [])

    def test_full_flow_changes_password_and_closes_sessions(self):
        self.s.forgot_password("A@b.co")
        token = self._token()
        self.s.reset_password(token, "NuevaClave99")
        self.assertTrue(self.s.login("a@b.co", "NuevaClave99").access_token)
        with self.assertRaises(svc.InvalidCredentials):
            self.s.login("a@b.co", PWD)
        with self.assertRaises(svc.InvalidRefreshToken):  # la sesion vieja se cerro
            self.s.refresh(self.out.refresh_token)

    def test_link_works_once(self):
        self.s.forgot_password("a@b.co")
        token = self._token()
        self.s.reset_password(token, "NuevaClave99")
        with self.assertRaises(svc.InvalidResetToken):
            self.s.reset_password(token, "OtraClave123")

    def test_link_expires(self):
        self.s.forgot_password("a@b.co")
        token = self._token()
        self.clock.advance(minutes=61)
        with self.assertRaises(svc.InvalidResetToken):
            self.s.reset_password(token, "NuevaClave99")

    def test_bad_token_and_weak_password(self):
        with self.assertRaises(svc.InvalidResetToken):
            self.s.reset_password("inventado", "NuevaClave99")
        self.s.forgot_password("a@b.co")
        with self.assertRaises(svc.InvalidInput):
            self.s.reset_password(self._token(), "corta")

    def test_mail_failure_is_swallowed(self):
        class Broken:
            def send_password_reset(self, *a):
                raise RuntimeError("smtp caido")

        self.s.mailer = Broken()
        self.s.forgot_password("a@b.co")  # no lanza: no se revela si la cuenta existe


class OAuthTests(unittest.TestCase):
    def setUp(self):
        self.profile = oauth.OAuthProfile("google", "g-123", "Nuevo@Mail.com", True, "Nuevo Usuario")
        self.provider = FakeProvider("google", True, self.profile)
        self.s, self.repo, self.mailer, self.clock, self.keys = make({"google": self.provider})

    def _start(self, role="entrepreneur"):
        url, nonce = self.s.oauth_start("google", role)
        state = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["state"][0]
        return state, nonce

    def test_first_login_creates_account_with_chosen_role(self):
        state, nonce = self._start("entrepreneur")
        out = self.s.oauth_finish("google", "code-1", state, nonce)
        self.assertEqual(out.account.email, "nuevo@mail.com")
        self.assertIsNone(out.account.password_hash)
        self.assertEqual(out.roles, ["entrepreneur"])
        self.assertEqual(self.repo.identities[0].provider_user_id, "g-123")

    def test_second_login_uses_the_identity_and_ignores_role(self):
        state, nonce = self._start("entrepreneur")
        first = self.s.oauth_finish("google", "c", state, nonce)
        state, nonce = self._start("visitor")
        second = self.s.oauth_finish("google", "c", state, nonce)
        self.assertEqual(first.account.id, second.account.id)
        self.assertEqual(second.roles, ["entrepreneur"])
        self.assertEqual(len(self.repo.accounts), 1)

    def test_existing_email_is_never_auto_linked(self):
        self.s.register("nuevo@mail.com", PWD, "Otro", "visitor")
        state, nonce = self._start()
        with self.assertRaises(svc.OAuthEmailConflict):
            self.s.oauth_finish("google", "c", state, nonce)
        self.assertEqual(self.repo.identities, [])

    def test_state_must_match_browser_nonce(self):
        state, _ = self._start()
        for bad_nonce in (None, "", "otro"):
            with self.assertRaises(oauth.OAuthFailed):
                self.s.oauth_finish("google", "c", state, bad_nonce)
        self.assertEqual(self.provider.calls, [])  # ni siquiera se llamo al proveedor

    def test_tampered_or_foreign_state(self):
        state, nonce = self._start()
        with self.assertRaises(oauth.OAuthFailed):
            self.s.oauth_finish("google", "c", state[:-3] + "abc", nonce)
        access = self.keys.sign(tokens.access_claims(1, "a@b.co", ["visitor"]))
        with self.assertRaises(oauth.OAuthFailed):  # un token de acceso no es un "state"
            self.s.oauth_finish("google", "c", access, nonce)

    def test_state_expires(self):
        state, nonce = self._start()
        self.clock.advance(minutes=11)
        # la expiracion la comprueba PyJWT con el reloj real: se firma uno vencido
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        old = self.keys.sign({"typ": "oauth_state", "provider": "google", "role": "visitor",
                              "nonce": nonce, "iss": tokens.ISSUER, "aud": tokens.STATE_AUDIENCE,
                              "iat": now - timedelta(hours=1), "exp": now - timedelta(minutes=50)})
        with self.assertRaises(oauth.OAuthFailed):
            self.s.oauth_finish("google", "c", old, nonce)

    def test_state_cannot_be_replayed_for_another_provider(self):
        fb = FakeProvider("facebook", True, oauth.OAuthProfile("facebook", "f1", "f@m.co", False, "F"))
        self.s.providers["facebook"] = fb
        state, nonce = self._start()  # state de google
        with self.assertRaises(oauth.OAuthFailed):
            self.s.oauth_finish("facebook", "c", state, nonce)

    def test_provider_errors(self):
        with self.assertRaises(svc.ProviderNotFound):
            self.s.oauth_start("twitter", "visitor")
        self.s.providers["facebook"] = FakeProvider("facebook", False)
        with self.assertRaises(svc.ProviderNotConfigured):
            self.s.oauth_start("facebook", "visitor")
        with self.assertRaises(svc.InvalidInput):
            self.s.oauth_start("google", "admin")

    def test_profile_without_email_is_refused(self):
        self.provider.profile = oauth.OAuthProfile("google", "g-9", None, False, "Sin Correo")
        state, nonce = self._start()
        with self.assertRaises(oauth.OAuthFailed):
            self.s.oauth_finish("google", "c", state, nonce)
        self.assertEqual(self.repo.accounts, {})

    def test_providers_status(self):
        self.s.providers["facebook"] = FakeProvider("facebook", False)
        self.assertEqual(self.s.providers_status(), {"google": True, "facebook": False})

    def test_authorize_url_is_built_with_public_callback(self):
        url, _ = self.s.oauth_start("google", "visitor")
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        self.assertEqual(q["redirect_uri"], ["http://app.test/api/v1/auth/oauth/google/callback"])


class ProviderUrlTests(unittest.TestCase):
    def test_google_and_facebook_urls_and_exchange(self):
        g = oauth.GoogleProvider(); g.client_id, g.client_secret = "cid", "sec"
        url = g.authorize_url("S", "http://x/cb")
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        self.assertEqual((q["client_id"], q["state"], q["redirect_uri"]), (["cid"], ["S"], ["http://x/cb"]))
        calls = []

        def http(method, u, data, headers):
            calls.append((method, u, data, headers))
            return {"access_token": "AT"} if "token" in u else {
                "sub": "42", "email": "e@x.co", "email_verified": True, "name": "N"}

        p = g.fetch_profile("CODE", "http://x/cb", http)
        self.assertEqual((p.subject, p.email, p.email_verified), ("42", "e@x.co", True))
        self.assertEqual(calls[0][2]["code"], "CODE")
        self.assertEqual(calls[1][3], {"Authorization": "Bearer AT"})

        f = oauth.FacebookProvider(); f.app_id, f.app_secret = "aid", "sec"
        self.assertTrue(f.authorize_url("S", "http://x/cb").startswith("https://www.facebook.com/"))
        http2 = lambda m, u, d, h: {"access_token": "AT"} if "access_token?" in u else {"id": "9", "name": "F", "email": "f@x.co"}
        pf = f.fetch_profile("C", "http://x/cb", http2)
        self.assertEqual((pf.subject, pf.email_verified), ("9", False))  # Facebook nunca "verificado"

    def test_unconfigured_when_env_missing(self):
        g = oauth.GoogleProvider(); g.client_id = g.client_secret = ""
        self.assertFalse(g.configured())

    def test_provider_without_token_fails(self):
        g = oauth.GoogleProvider(); g.client_id, g.client_secret = "a", "b"
        with self.assertRaises(oauth.OAuthFailed):
            g.fetch_profile("C", "http://x", lambda *a: {})


if __name__ == "__main__":
    unittest.main()
