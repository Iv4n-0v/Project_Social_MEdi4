import unittest

import service as svc
from schemas import VentureSave
from tests.fakes import FakeRepo


def make():
    repo = FakeRepo()
    svc.seed_categories(repo)
    return svc.VentureService(repo), repo


def data(**kw):
    base = dict(name="Dulce Hogar", description="Postres caseros")
    base.update(kw)
    return VentureSave(**base)


def published(s, account=1, **kw):
    v, _ = s.save_mine(account, data(**kw))
    s.publish(account)
    return v


class SeedTests(unittest.TestCase):
    def test_seed_only_when_empty(self):
        s, repo = make()
        n = len(repo.cats)
        self.assertEqual(n, len(svc.DEFAULT_CATEGORIES))
        svc.seed_categories(repo)
        self.assertEqual(len(repo.cats), n)


class SaveTests(unittest.TestCase):
    def test_create_is_hidden_draft_with_audit(self):
        s, repo = make()
        v, created = s.save_mine(1, data())
        self.assertTrue(created)
        self.assertFalse(v.is_published)
        self.assertEqual([a.action for a in repo.audit_rows], ["CREATE"])

    def test_second_save_updates_not_duplicates(self):
        s, repo = make()
        s.save_mine(1, data())
        v, created = s.save_mine(1, data(name="Nuevo"))
        self.assertFalse(created)
        self.assertEqual(v.name, "Nuevo")
        self.assertEqual(len(repo.ventures), 1)

    def test_invalid_category(self):
        s, _ = make()
        with self.assertRaises(svc.InvalidInput):
            s.save_mine(1, data(category_id=999))

    def test_get_mine_without_venture(self):
        s, _ = make()
        with self.assertRaises(svc.VentureNotFound):
            s.get_mine(1)

    def test_accounts_are_isolated(self):
        s, _ = make()
        s.save_mine(1, data(name="A"))
        s.save_mine(2, data(name="B"))
        self.assertEqual(s.get_mine(1).name, "A")
        self.assertEqual(s.get_mine(2).name, "B")


class PublishTests(unittest.TestCase):
    def test_publish_requires_description(self):
        s, _ = make()
        s.save_mine(1, data(description=None))
        with self.assertRaises(svc.NotPublishable):
            s.publish(1)

    def test_publish_makes_it_public_and_unpublish_hides_it(self):
        s, _ = make()
        v = published(s)
        self.assertEqual(s.get_public(v.id).name, "Dulce Hogar")
        s.unpublish(1)
        with self.assertRaises(svc.VentureNotFound):
            s.get_public(v.id)

    def test_draft_is_not_public(self):
        s, _ = make()
        v, _ = s.save_mine(1, data())
        with self.assertRaises(svc.VentureNotFound):
            s.get_public(v.id)
        self.assertEqual(s.search(None, None, 10, 0).total, 0)

    def test_delete_hides_and_restore_returns_as_draft(self):
        s, repo = make()
        v = published(s)
        s.delete_mine(1)
        with self.assertRaises(svc.VentureNotFound):
            s.get_public(v.id)
        with self.assertRaises(svc.VentureInactive):
            s.save_mine(1, data(name="X"))
        r = s.restore_mine(1)
        self.assertTrue(r.is_active)
        self.assertFalse(r.is_published)  # vuelve oculto: el emprendedor decide publicar
        self.assertIn("DELETE", [a.action for a in repo.audit_rows])
        self.assertIn("RESTORE", [a.action for a in repo.audit_rows])


class PrivacyTests(unittest.TestCase):
    def test_entrepreneur_name_hidden_unless_authorized(self):
        s, _ = make()
        v = published(s, entrepreneur_name="Ana Perez")
        self.assertIsNone(s.get_public(v.id).entrepreneur_name)
        self.assertEqual(s.get_mine(1).entrepreneur_name, "Ana Perez")
        s.save_mine(1, data(entrepreneur_name="Ana Perez", show_entrepreneur_name=True))
        self.assertEqual(s.get_public(v.id).entrepreneur_name, "Ana Perez")

    def test_public_view_has_no_owner_id(self):
        s, _ = make()
        v = published(s)
        self.assertNotIn("owner_account_id", s.get_public(v.id).model_dump())


class SearchTests(unittest.TestCase):
    def test_search_by_name_and_category_and_paging(self):
        s, _ = make()
        published(s, 1, name="Pasteleria Luna", category_id=2)
        published(s, 2, name="Taller Sol", description="Joyeria", category_id=5)
        published(s, 3, name="Luna Moda", description="Ropa", category_id=1)
        self.assertEqual(s.search("luna", None, 10, 0).total, 2)
        self.assertEqual(s.search(None, 5, 10, 0).total, 1)
        self.assertEqual(s.search("luna", 1, 10, 0).items[0].name, "Luna Moda")
        page = s.search(None, None, 2, 0)
        self.assertEqual((len(page.items), page.total), (2, 3))
        self.assertEqual(len(s.search(None, None, 2, 2).items), 1)

    def test_limit_is_capped(self):
        s, _ = make()
        self.assertEqual(s.search(None, None, 9999, 0).limit, svc.MAX_PAGE)


class SocialTests(unittest.TestCase):
    def test_valid_link_with_manual_followers(self):
        s, _ = make()
        v = published(s)
        s.set_social(1, "instagram", "https://www.instagram.com/dulcehogar", 1200)
        soc = s.get_public(v.id).social[0]
        self.assertEqual((soc.platform, soc.followers, soc.followers_source), ("instagram", 1200, "manual"))

    def test_no_followers_means_none_not_zero(self):
        s, _ = make()
        v = published(s)
        s.set_social(1, "whatsapp", "https://wa.me/573001112233", None)
        soc = s.get_public(v.id).social[0]
        self.assertIsNone(soc.followers)
        self.assertIsNone(soc.followers_source)

    def test_wrong_domain_rejected(self):
        s, _ = make()
        published(s)
        for platform, url in [
            ("instagram", "https://evil.com/instagram.com"),
            ("instagram", "https://instagram.com.evil.com/x"),
            ("facebook", "javascript:alert(1)"),
            ("tiktok", "ftp://tiktok.com/x"),
            ("myspace", "https://instagram.com/x"),
        ]:
            with self.assertRaises(svc.InvalidInput, msg=url):
                s.set_social(1, platform, url, None)

    def test_update_keeps_one_link_and_latest_followers_win(self):
        s, repo = make()
        v = published(s)
        s.set_social(1, "youtube", "https://youtube.com/@a", 10)
        s.set_social(1, "youtube", "https://youtu.be/b", 20)
        self.assertEqual(len(s.get_public(v.id).social), 1)
        self.assertEqual(s.get_public(v.id).social[0].followers, 20)

    def test_remove_is_logical_and_relink_works(self):
        s, repo = make()
        v = published(s)
        s.set_social(1, "tiktok", "https://tiktok.com/@a", None)
        s.remove_social(1, "tiktok")
        self.assertEqual(s.get_public(v.id).social, [])
        self.assertEqual(len(repo.links), 1)  # se conserva
        s.set_social(1, "tiktok", "https://tiktok.com/@a", None)
        self.assertEqual(len(s.get_public(v.id).social), 1)
        self.assertEqual(len(repo.links), 1)

    def test_social_needs_venture(self):
        s, _ = make()
        with self.assertRaises(svc.VentureNotFound):
            s.set_social(1, "instagram", "https://instagram.com/a", None)


class StatsTests(unittest.TestCase):
    def test_no_data_is_none_never_zero(self):
        s, _ = make()
        published(s)
        s.set_social(1, "instagram", "https://instagram.com/a", None)
        st = s.stats_mine(1)
        self.assertEqual(len(st), 1)
        self.assertIsNone(st[0].latest)
        self.assertEqual(st[0].history, [])

    def test_history_newest_first_with_source_and_date(self):
        s, _ = make()
        published(s)
        for n in (100, 150, 200):
            s.set_social(1, "instagram", "https://instagram.com/a", n)
        st = s.stats_mine(1)[0]
        self.assertEqual([p.followers for p in st.history], [200, 150, 100])
        self.assertEqual(st.latest.followers, 200)
        self.assertEqual(st.latest.source, "manual")
        self.assertIsNotNone(st.latest.updated_at)

    def test_history_is_capped_and_unlinked_networks_hidden(self):
        s, _ = make()
        published(s)
        for n in range(15):
            s.set_social(1, "youtube", "https://youtube.com/@a", n)
        self.assertEqual(len(s.stats_mine(1)[0].history), s.HISTORY_LIMIT)
        s.remove_social(1, "youtube")
        self.assertEqual(s.stats_mine(1), [])

    def test_stats_need_a_venture_and_are_private(self):
        s, _ = make()
        with self.assertRaises(svc.VentureNotFound):
            s.stats_mine(1)
        published(s, 1)
        s.set_social(1, "tiktok", "https://tiktok.com/@a", 5)
        with self.assertRaises(svc.VentureNotFound):
            s.stats_mine(2)


class FavoriteTests(unittest.TestCase):
    def test_add_list_remove_and_idempotent(self):
        s, repo = make()
        v = published(s, 1)
        s.add_favorite(9, v.id)
        s.add_favorite(9, v.id)
        self.assertEqual(s.favorite_ids(9), [v.id])
        self.assertEqual([x.id for x in s.list_favorites(9)], [v.id])
        s.remove_favorite(9, v.id)
        s.remove_favorite(9, v.id)
        self.assertEqual(s.favorite_ids(9), [])

    def test_favorites_are_private_per_account(self):
        s, _ = make()
        v = published(s, 1)
        s.add_favorite(9, v.id)
        self.assertEqual(s.favorite_ids(8), [])

    def test_cannot_favorite_draft_or_missing(self):
        s, _ = make()
        d, _ = s.save_mine(1, data())
        for vid in (d.id, 999):
            with self.assertRaises(svc.VentureNotFound):
                s.add_favorite(9, vid)

    def test_unpublished_venture_disappears_from_list(self):
        s, _ = make()
        v = published(s, 1)
        s.add_favorite(9, v.id)
        s.unpublish(1)
        self.assertEqual(s.list_favorites(9), [])


if __name__ == "__main__":
    unittest.main()
