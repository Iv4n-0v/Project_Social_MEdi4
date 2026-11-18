"""Fase 6: foto del emprendimiento y conexion oficial con YouTube (sin red real)."""
import asyncio
import time
import unittest
import urllib.parse

import jwt

import service as svc
import youtube
from schemas import VentureSave
from storage import StorageUnavailable
from tests.fakes import FakeRepo

JPEG = b"\xff\xd8\xff\xe0" + b"0" * 100
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100
WEBP = b"RIFF" + b"\x00" * 4 + b"WEBP" + b"0" * 50


class FakeStorage:
    def __init__(self, configured=True):
        self.configured, self.uploaded, self.deleted = configured, [], []

    def is_configured(self):
        return self.configured

    async def upload(self, content, extension, content_type, folder):
        url = f"https://cdn.test/{folder}/{len(self.uploaded)}{extension}"
        self.uploaded.append((url, content_type))
        return url

    async def delete(self, url):
        self.deleted.append(url)


class FakeHttp:
    """Respuestas de Google/YouTube preparadas; guarda las llamadas."""

    def __init__(self, channel=None, token="tok"):
        self.calls, self.token = [], token
        self.channel = channel if channel is not None else {
            "items": [{"id": "UC123", "snippet": {"title": "Mi canal"}, "statistics": {"subscriberCount": "1520"}}]
        }

    def __call__(self, method, url, data=None, headers=None):
        self.calls.append((method, url, data, headers))
        if "oauth2.googleapis.com" in url:
            return {"access_token": self.token} if self.token else {}
        return self.channel


def connector(http=None, clock=None):
    return youtube.YoutubeConnector("cid", "csecret", "https://app.test/", "state-secret", http or FakeHttp(), clock or time.time)


def make():
    repo = FakeRepo()
    svc.seed_categories(repo)
    s = svc.VentureService(repo)
    s.save_mine(1, VentureSave(name="Dulce Hogar", description="Postres"))
    return s, repo


def run(coro):
    return asyncio.run(coro)


class ImageTests(unittest.TestCase):
    def test_sniff_by_content(self):
        self.assertEqual(svc.sniff_image(JPEG), "jpeg")
        self.assertEqual(svc.sniff_image(PNG), "png")
        self.assertEqual(svc.sniff_image(WEBP), "webp")
        self.assertIsNone(svc.sniff_image(b"<svg onload=alert(1)>"))
        self.assertIsNone(svc.sniff_image(b"GIF89a"))

    def test_upload_saves_url_audit_and_deletes_old(self):
        s, repo = make()
        st = FakeStorage()
        v = run(s.set_image(1, JPEG, st))
        self.assertEqual(v.profile_image_url, "https://cdn.test/emprendimientos/1/0.jpg")
        self.assertEqual(st.uploaded[0][1], "image/jpeg")
        v = run(s.set_image(1, PNG, st))
        self.assertEqual(st.deleted, ["https://cdn.test/emprendimientos/1/0.jpg"])
        self.assertIn("IMAGE_SET", [a.action for a in repo.audit_rows])

    def test_extension_comes_from_content_not_client(self):
        s, _ = make()
        st = FakeStorage()
        run(s.set_image(1, PNG, st))
        self.assertTrue(st.uploaded[0][0].endswith(".png"))

    def test_rejects_invalid(self):
        s, _ = make()
        st = FakeStorage()
        for bad in (b"", b"hola mundo", b"<html>", JPEG + b"0" * svc.MAX_IMAGE_BYTES):
            with self.assertRaises(svc.InvalidInput):
                run(s.set_image(1, bad, st))
        self.assertEqual(st.uploaded, [])

    def test_storage_not_configured(self):
        s, _ = make()
        with self.assertRaises(StorageUnavailable):
            run(s.set_image(1, JPEG, FakeStorage(configured=False)))

    def test_only_own_venture(self):
        s, _ = make()
        with self.assertRaises(svc.VentureNotFound):
            run(s.set_image(99, JPEG, FakeStorage()))

    def test_remove_image(self):
        s, repo = make()
        st = FakeStorage()
        run(s.set_image(1, JPEG, st))
        v = run(s.remove_image(1, st))
        self.assertIsNone(v.profile_image_url)
        self.assertEqual(len(st.deleted), 1)
        run(s.remove_image(1, st))  # idempotente
        self.assertEqual(len(st.deleted), 1)


class YoutubeUrlTests(unittest.TestCase):
    def test_authorize_url_is_read_only_and_signed(self):
        url = connector().authorize_url(7)
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        self.assertEqual(q["scope"], [youtube.SCOPE])
        self.assertTrue(q["scope"][0].endswith("youtube.readonly"))
        self.assertEqual(q["redirect_uri"], ["https://app.test/api/v1/youtube/callback"])
        self.assertEqual(q["access_type"], ["online"])  # sin refresh token
        self.assertEqual(connector().account_from_state(q["state"][0]), 7)

    def test_not_configured(self):
        with self.assertRaises(youtube.NotConfigured):
            youtube.YoutubeConnector().authorize_url(1)

    def test_state_rejected_when_tampered_expired_or_foreign(self):
        c = connector()
        state = urllib.parse.parse_qs(urllib.parse.urlparse(c.authorize_url(7)).query)["state"][0]
        with self.assertRaises(youtube.InvalidState):
            c.account_from_state(state + "x")
        old = urllib.parse.parse_qs(urllib.parse.urlparse(
            connector(clock=lambda: time.time() - 601).authorize_url(7)).query)["state"][0]
        with self.assertRaises(youtube.InvalidState):
            c.account_from_state(old)  # emitido hace mas de 10 min
        other = youtube.YoutubeConnector("cid", "csecret", "https://app.test", "otro-secreto")
        with self.assertRaises(youtube.InvalidState):
            other.account_from_state(state)
        forged = jwt.encode({"sub": "7", "aud": "otra-cosa", "exp": 99999999999}, "state-secret", algorithm="HS256")
        with self.assertRaises(youtube.InvalidState):
            c.account_from_state(forged)
        with self.assertRaises(youtube.InvalidState):
            c.account_from_state("")

    def test_state_none_algorithm_rejected(self):
        c = connector()
        bad = jwt.encode({"sub": "7", "aud": youtube.STATE_AUDIENCE, "exp": 99999999999}, None, algorithm="none")
        with self.assertRaises(youtube.InvalidState):
            c.account_from_state(bad)


class YoutubeFlowTests(unittest.TestCase):
    def state(self, c, account=1):
        return urllib.parse.parse_qs(urllib.parse.urlparse(c.authorize_url(account)).query)["state"][0]

    def test_ok_saves_api_stat_and_link(self):
        s, repo = make()
        c = connector()
        self.assertEqual(s.youtube_finish("code", self.state(c), None, c), "ok")
        stats = s.stats_mine(1)
        self.assertEqual(stats[0].platform, "youtube")
        self.assertEqual(stats[0].url, "https://www.youtube.com/channel/UC123")
        self.assertEqual((stats[0].latest.followers, stats[0].latest.source), (1520, "api"))
        self.assertIn("YOUTUBE_SYNC", [a.action for a in repo.audit_rows])

    def test_token_never_stored_and_sent_only_to_youtube(self):
        s, repo = make()
        http = FakeHttp(token="SECRET-TOKEN")
        c = connector(http)
        s.youtube_finish("code", self.state(c), None, c)
        blob = repr(repo.links) + repr(repo.stats) + repr([a.action for a in repo.audit_rows])
        self.assertNotIn("SECRET-TOKEN", blob)
        self.assertEqual(http.calls[1][3], {"Authorization": "Bearer SECRET-TOKEN"})
        self.assertIn("mine=true", http.calls[1][1])

    def test_second_sync_adds_history_and_reuses_link(self):
        s, _ = make()
        c = connector()
        s.youtube_finish("c", self.state(c), None, c)
        s.youtube_finish("c", self.state(c), None, c)
        stat = s.stats_mine(1)[0]
        self.assertEqual(len(stat.history), 2)
        self.assertEqual(len(s.stats_mine(1)), 1)

    def test_hidden_count_saves_nothing(self):
        s, repo = make()
        ch = {"items": [{"id": "UC1", "snippet": {}, "statistics": {"hiddenSubscriberCount": True}}]}
        c = connector(FakeHttp(channel=ch))
        self.assertEqual(s.youtube_finish("c", self.state(c), None, c), "hidden")
        self.assertEqual(repo.stats, [])
        self.assertEqual(repo.links, [])

    def test_no_channel(self):
        s, repo = make()
        c = connector(FakeHttp(channel={"items": []}))
        self.assertEqual(s.youtube_finish("c", self.state(c), None, c), "nochannel")
        self.assertEqual(repo.stats, [])

    def test_denied_invalid_failed(self):
        s, repo = make()
        c = connector()
        self.assertEqual(s.youtube_finish(None, self.state(c), "access_denied", c), "denied")
        self.assertEqual(s.youtube_finish("c", "basura", None, c), "invalid")
        self.assertEqual(s.youtube_finish("c", None, None, c), "invalid")
        self.assertEqual(s.youtube_finish("c", self.state(c), None, connector(FakeHttp(token=None))), "failed")
        self.assertEqual(repo.stats, [])

    def test_state_decides_account_not_caller(self):
        s, repo = make()
        c = connector()
        s.save_mine(2, VentureSave(name="Otro", description="x"))
        s.youtube_finish("c", self.state(c, account=2), None, c)
        self.assertEqual(s.stats_mine(1), [])
        self.assertEqual(s.stats_mine(2)[0].latest.followers, 1520)

    def test_no_venture(self):
        s, _ = make()
        c = connector()
        self.assertEqual(s.youtube_finish("c", self.state(c, account=55), None, c), "novenue")
        with self.assertRaises(svc.VentureNotFound):
            s.youtube_start(55, c)


if __name__ == "__main__":
    unittest.main()
