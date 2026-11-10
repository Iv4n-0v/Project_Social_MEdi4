"""Cada cuenta ve y modifica solo sus propios analisis (sin base de datos)."""
import unittest

import service as svc
from models import Analysis
from schemas import AnalysisCreate, AnalysisUpdate


class FakeRepo:
    def __init__(self):
        self.rows, self.audit_rows, self._n = {}, [], 1

    def find_all(self, owner, is_active=None, user_id=None):
        return [a for a in self.rows.values() if a.owner_account_id == owner
                and (is_active is None or a.is_active == is_active)
                and (user_id is None or a.user_id == user_id)]

    def get(self, aid):
        return self.rows.get(aid)

    def add(self, a):
        a.id = self._n
        self._n += 1
        self.rows[a.id] = a
        return a

    def add_audit(self, aid, action):
        self.audit_rows.append((aid, action))

    def audits(self, aid):
        return [a for a in self.audit_rows if a[0] == aid]

    def commit(self):
        pass

    def refresh(self, obj):
        pass


def make():
    return svc.AnalysisService(FakeRepo())


def create(s, owner, sector="Moda", user_id=1):
    return s.create_analysis(owner, AnalysisCreate(sector=sector, reach=10, time_in_social_media=1.5, user_id=user_id))


class OwnerTests(unittest.TestCase):
    def test_list_only_returns_own_and_still_filters_by_user(self):
        s = make()
        create(s, 1, "A", 5)
        create(s, 1, "B", 6)
        create(s, 2, "C", 5)
        self.assertEqual(sorted(a.sector for a in s.list_analyses(1)), ["A", "B"])
        self.assertEqual([a.sector for a in s.list_analyses(1, None, 5)], ["A"])
        self.assertEqual([a.sector for a in s.list_analyses(2)], ["C"])

    def test_legacy_records_without_owner_are_invisible(self):
        s = make()
        s.repo.add(Analysis(sector="viejo", reach=1, time_in_social_media=1, user_id=1))
        self.assertEqual(s.list_analyses(1), [])

    def test_foreign_record_is_404_for_every_operation(self):
        s = make()
        mine = create(s, 1)
        for call in (
            lambda: s.get_analysis(mine.id, 2),
            lambda: s.update_analysis(mine.id, 2, AnalysisUpdate(sector="x")),
            lambda: s.delete_analysis(mine.id, 2),
            lambda: s.restore_analysis(mine.id, 2),
            lambda: s.audits(mine.id, 2),
        ):
            with self.assertRaises(svc.AnalysisNotFound):
                call()
        self.assertEqual(s.get_analysis(mine.id, 1).sector, "Moda")

    def test_owner_flow(self):
        s = make()
        a = create(s, 1)
        self.assertEqual(s.update_analysis(a.id, 1, AnalysisUpdate(reach=99)).reach, 99)
        self.assertFalse(s.delete_analysis(a.id, 1).is_active)
        self.assertTrue(s.restore_analysis(a.id, 1).is_active)
        self.assertEqual([x[1] for x in s.audits(a.id, 1)], ["CREATE", "UPDATE", "DELETE", "RESTORE"])


if __name__ == "__main__":
    unittest.main()
