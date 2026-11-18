"""Cada cuenta ve y modifica solo sus propios usuarios (sin base de datos)."""
import asyncio
import unittest

import service as svc
from models import User
from schemas import UserUpdate


class FakeRepo:
    def __init__(self):
        self.users, self.links, self.audit_rows, self._n = {}, {}, [], 1

    def find_all(self, owner, is_active=None):
        return [u for u in self.users.values()
                if u.owner_account_id == owner and (is_active is None or u.is_active == is_active)]

    def get(self, uid):
        return self.users.get(uid)

    def add(self, user):
        user.id = self._n
        self._n += 1
        self.users[user.id] = user
        return user

    def methodology_ids(self, uid):
        return sorted(self.links.get(uid, []))

    def set_methodologies(self, uid, ids):
        self.links[uid] = set(ids)

    def add_audit(self, uid, action):
        self.audit_rows.append((uid, action))

    def audits(self, uid):
        return [a for a in self.audit_rows if a[0] == uid]

    def commit(self):
        pass

    def refresh(self, obj):
        pass


class NoStorage:
    async def upload(self, *a, **k):
        raise AssertionError("no deberia subir nada")


def make():
    return svc.UserService(FakeRepo(), NoStorage())


def create(s, owner, name):
    return asyncio.run(s.create_user(owner, name, True, []))


class OwnerTests(unittest.TestCase):
    def test_list_only_returns_own(self):
        s = make()
        create(s, 1, "de Ana")
        create(s, 2, "de Beto")
        self.assertEqual([u.name for u in s.list_users(1)], ["de Ana"])
        self.assertEqual([u.name for u in s.list_users(2)], ["de Beto"])

    def test_legacy_records_without_owner_are_invisible(self):
        s = make()
        s.repo.add(User(name="viejo", is_active=True))
        self.assertEqual(s.list_users(1), [])
        with self.assertRaises(svc.UserNotFound):
            s.get_user(1, 1)

    def test_foreign_record_is_404_for_every_operation(self):
        s = make()
        mine = create(s, 1, "de Ana")
        for call in (
            lambda: s.get_user(mine.id, 2),
            lambda: s.update_user(mine.id, 2, UserUpdate(name="x")),
            lambda: s.delete_user(mine.id, 2),
            lambda: s.restore_user(mine.id, 2),
            lambda: s.audits(mine.id, 2),
            lambda: asyncio.run(s.update_image(mine.id, 2, b"x", "a.png", "image/png")),
        ):
            with self.assertRaises(svc.UserNotFound):
                call()
        self.assertEqual(s.get_user(mine.id, 1).name, "de Ana")  # intacto

    def test_owner_can_delete_and_restore(self):
        s = make()
        u = create(s, 1, "x")
        self.assertFalse(s.delete_user(u.id, 1).is_active)
        self.assertEqual(s.list_users(1, True), [])
        self.assertTrue(s.restore_user(u.id, 1).is_active)

    def test_owner_comes_from_the_argument_not_from_the_body(self):
        s = make()
        u = create(s, 7, "x")
        self.assertEqual(s.repo.users[u.id].owner_account_id, 7)


if __name__ == "__main__":
    unittest.main()
