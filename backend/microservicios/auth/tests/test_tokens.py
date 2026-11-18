import base64
import datetime
import os
import tempfile
import unittest

import jwt

import tokens


class TokenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.keys = tokens.KeyManager()

    def test_sign_and_verify(self):
        t = self.keys.sign(tokens.access_claims(7, "a@b.co", ["visitor", "entrepreneur"]))
        claims = self.keys.verify(t)
        self.assertEqual(claims["sub"], "7")
        self.assertEqual(claims["roles"], ["entrepreneur", "visitor"])
        self.assertEqual(claims["iss"], tokens.ISSUER)

    def test_header_has_kid_matching_jwks(self):
        t = self.keys.sign(tokens.access_claims(1, "a@b.co", []))
        header = jwt.get_unverified_header(t)
        self.assertEqual(header["alg"], "RS256")
        self.assertEqual(header["kid"], self.keys.jwks()["keys"][0]["kid"])

    def test_jwks_shape_has_only_public_parts(self):
        key = self.keys.jwks()["keys"][0]
        self.assertEqual({"kty", "use", "alg", "kid", "n", "e"}, set(key))
        self.assertEqual(key["kty"], "RSA")
        for private_part in ("d", "p", "q", "dp", "dq", "qi"):
            self.assertNotIn(private_part, key)
        base64.urlsafe_b64decode(key["n"] + "==")  # es base64url valido

    def test_expired_token_is_rejected(self):
        claims = tokens.access_claims(1, "a@b.co", [])
        claims["exp"] = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=5)
        with self.assertRaises(tokens.InvalidToken):
            self.keys.verify(self.keys.sign(claims))

    def test_token_signed_by_other_key_is_rejected(self):
        other = tokens.KeyManager()
        with self.assertRaises(tokens.InvalidToken):
            self.keys.verify(other.sign(tokens.access_claims(1, "a@b.co", [])))

    def test_tampered_token_is_rejected(self):
        t = self.keys.sign(tokens.access_claims(1, "a@b.co", ["visitor"]))
        head, body, sig = t.split(".")
        with self.assertRaises(tokens.InvalidToken):
            self.keys.verify(f"{head}.{body[:-2]}xx.{sig}")

    def test_state_audience_is_not_an_access_token(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        state = self.keys.sign(
            {"typ": "oauth_state", "iss": tokens.ISSUER, "aud": tokens.STATE_AUDIENCE,
             "iat": now, "exp": now + datetime.timedelta(minutes=5)}
        )
        with self.assertRaises(tokens.InvalidToken):
            self.keys.verify(state)  # como token de acceso: rechazado
        self.assertEqual(self.keys.verify(state, audience=tokens.STATE_AUDIENCE)["typ"], "oauth_state")

    def test_key_is_persisted_between_restarts(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "sub", "jwt.pem")
            os.environ["JWT_KEY_FILE"] = path
            os.environ.pop("JWT_PRIVATE_KEY", None)
            try:
                first = tokens.load_key_manager()
                self.assertTrue(os.path.exists(path))
                second = tokens.load_key_manager()
                self.assertEqual(first.kid, second.kid)
                self.assertEqual(oct(os.stat(path).st_mode & 0o777), "0o600")
            finally:
                os.environ.pop("JWT_KEY_FILE", None)

    def test_key_from_env_variable(self):
        base = tokens.KeyManager()
        os.environ["JWT_PRIVATE_KEY"] = base.private_pem().decode().replace("\n", "\\n")
        try:
            self.assertEqual(tokens.load_key_manager().kid, base.kid)
        finally:
            os.environ.pop("JWT_PRIVATE_KEY", None)


if __name__ == "__main__":
    unittest.main()
