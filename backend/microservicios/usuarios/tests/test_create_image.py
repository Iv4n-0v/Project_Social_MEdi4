"""Creacion de usuarios con y sin imagen, y validacion de la imagen (sin base de datos)."""
import asyncio
import unittest

import service as svc
from tests.test_owner import FakeRepo


class FakeStorage:
    """Registra las subidas y devuelve una URL falsa, sin tocar el bucket real."""

    def __init__(self):
        self.calls = []

    async def upload(self, content, filename, content_type, folder):
        self.calls.append((filename, content_type, folder))
        return f"https://bucket.test/{folder}/{filename}"


def make():
    storage = FakeStorage()
    return svc.UserService(FakeRepo(), storage), storage


def create(s, name="Ana", image=None):
    return asyncio.run(s.create_user(1, name, True, [], image))


class CreateWithoutImageTests(unittest.TestCase):
    def test_creates_user_without_image(self):
        s, storage = make()
        u = create(s)
        self.assertIsNone(u.img)
        self.assertEqual(storage.calls, [])  # no se sube nada

    def test_without_image_still_writes_audit_and_trims_name(self):
        s, _ = make()
        u = create(s, name="  Ana  ")
        self.assertEqual(u.name, "Ana")
        self.assertEqual(s.repo.audits(u.id), [(u.id, "CREATE")])


class CreateWithImageTests(unittest.TestCase):
    def test_valid_image_is_uploaded_to_users_folder(self):
        s, storage = make()
        u = create(s, image=(b"data", "foto.png", "image/png"))
        self.assertEqual(storage.calls, [("foto.png", "image/png", "users")])
        self.assertEqual(u.img, "https://bucket.test/users/foto.png")

    def test_unsupported_type_is_rejected_and_nothing_is_created(self):
        s, storage = make()
        with self.assertRaises(svc.UnsupportedImageType):
            create(s, image=(b"data", "x.pdf", "application/pdf"))
        self.assertEqual(s.repo.users, {})
        self.assertEqual(storage.calls, [])

    def test_empty_image_is_rejected(self):
        s, _ = make()
        with self.assertRaises(svc.EmptyImage):
            create(s, image=(b"", "x.png", "image/png"))
        self.assertEqual(s.repo.users, {})

    def test_image_over_5mb_is_rejected(self):
        s, _ = make()
        big = b"0" * (svc.MAX_IMAGE_BYTES + 1)
        with self.assertRaises(svc.ImageTooLarge):
            create(s, image=(big, "x.png", "image/png"))
        self.assertEqual(s.repo.users, {})


if __name__ == "__main__":
    unittest.main()
