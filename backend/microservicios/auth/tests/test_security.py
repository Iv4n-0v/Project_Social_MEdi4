import unittest

import security


class PasswordTests(unittest.TestCase):
    def test_hash_and_verify(self):
        h = security.hash_password("Clave12345")
        self.assertTrue(h.startswith("scrypt$"))
        self.assertNotIn("Clave12345", h)
        self.assertTrue(security.verify_password("Clave12345", h))
        self.assertFalse(security.verify_password("clave12345", h))

    def test_same_password_gets_different_hashes(self):
        self.assertNotEqual(security.hash_password("Clave12345"), security.hash_password("Clave12345"))

    def test_account_without_password_never_matches(self):
        self.assertFalse(security.verify_password("lo-que-sea", None))
        self.assertFalse(security.verify_password("lo-que-sea", ""))

    def test_corrupt_hash_is_rejected_not_crash(self):
        self.assertFalse(security.verify_password("x", "no-es-un-hash"))
        self.assertFalse(security.verify_password("x", "scrypt$a$b$c$d$e"))

    def test_policy(self):
        self.assertIsNotNone(security.password_problem("corta"))
        self.assertIsNotNone(security.password_problem("x" * 129))
        self.assertIsNone(security.password_problem("suficiente1"))

    def test_email(self):
        self.assertEqual(security.normalize_email("  Ana@Mail.COM "), "ana@mail.com")
        self.assertTrue(security.is_valid_email("ana@mail.com"))
        for bad in ("", "sin-arroba", "a@b", "a b@c.co", "@c.co"):
            self.assertFalse(security.is_valid_email(bad), bad)


class OpaqueTokenTests(unittest.TestCase):
    def test_tokens_are_random_and_hash_is_stable(self):
        a, b = security.new_opaque_token(), security.new_opaque_token()
        self.assertNotEqual(a, b)
        self.assertEqual(security.hash_token(a), security.hash_token(a))
        self.assertNotEqual(security.hash_token(a), a)


class ThrottleTests(unittest.TestCase):
    def test_blocks_after_limit_and_recovers(self):
        t = [0.0]
        th = security.LoginThrottle(max_failures=3, window_seconds=60, clock=lambda: t[0])
        for _ in range(3):
            self.assertFalse(th.blocked("a@b.co"))
            th.record_failure("a@b.co")
        self.assertTrue(th.blocked("a@b.co"))
        self.assertFalse(th.blocked("otro@b.co"))
        t[0] = 61  # pasa la ventana
        self.assertFalse(th.blocked("a@b.co"))

    def test_clear(self):
        th = security.LoginThrottle(max_failures=1)
        th.record_failure("a@b.co")
        self.assertTrue(th.blocked("a@b.co"))
        th.clear("a@b.co")
        self.assertFalse(th.blocked("a@b.co"))


if __name__ == "__main__":
    unittest.main()
