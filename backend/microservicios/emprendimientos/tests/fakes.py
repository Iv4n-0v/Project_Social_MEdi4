"""Repositorio falso en memoria con la misma interfaz que VentureRepository."""
import datetime

from models import Category, Favorite, FollowerStat, SocialLink, Venture, VentureAudit
from repository import DuplicateVenture


class FakeRepo:
    def __init__(self) -> None:
        self.cats, self.ventures, self.links, self.stats = {}, {}, [], []
        self.favs, self.audit_rows = [], []
        self.commits = 0
        self._ids = {"cat": 1, "v": 1, "l": 1, "s": 1, "a": 1}

    def _next(self, k):
        n = self._ids[k]
        self._ids[k] += 1
        return n

    def commit(self):
        self.commits += 1

    def save(self, obj):
        pass  # los objetos ya viven en memoria

    # categorias
    def categories(self, only_active=True):
        return [c for c in self.cats.values() if c.is_active or not only_active]

    def get_category(self, cid):
        return self.cats.get(cid)

    def count_categories(self):
        return len(self.cats)

    def add_category(self, name):
        c = Category(name=name)
        c.id = self._next("cat")
        self.cats[c.id] = c
        return c

    # emprendimientos
    def get_venture(self, vid):
        return self.ventures.get(vid)

    def get_by_owner(self, account_id):
        return next((v for v in self.ventures.values() if v.owner_account_id == account_id), None)

    def add_venture(self, v):
        if self.get_by_owner(v.owner_account_id):
            raise DuplicateVenture()
        v.id = self._next("v")
        self.ventures[v.id] = v
        return v

    def _public(self):
        return [v for v in self.ventures.values() if v.is_published and v.is_active]

    def search_public(self, q, category_id, limit, offset):
        rows = self._public()
        if category_id is not None:
            rows = [v for v in rows if v.category_id == category_id]
        if q:
            q = q.lower()
            rows = [v for v in rows if q in v.name.lower() or q in (v.description or "").lower()]
        rows.sort(key=lambda v: -v.id)
        return rows[offset:offset + limit], len(rows)

    def public_by_ids(self, ids):
        return [v for v in self._public() if v.id in ids]

    # redes
    def links_for(self, vids):
        return [l for l in self.links if l.venture_id in vids and l.is_active]

    def get_link(self, vid, platform):
        return next((l for l in self.links if l.venture_id == vid and l.platform == platform), None)

    def add_link(self, link):
        link.id = self._next("l")
        self.links.append(link)
        return link

    def latest_stats(self, link_ids):
        return {s.social_link_id: s for s in self.stats if s.social_link_id in link_ids}

    def add_stat(self, stat):
        stat.id = self._next("s")
        self.stats.append(stat)

    # favoritos
    def favorite_ids(self, account_id):
        return [v for (a, v) in reversed(self.favs) if a == account_id]

    def has_favorite(self, account_id, vid):
        return (account_id, vid) in self.favs

    def add_favorite(self, account_id, vid):
        self.favs.append((account_id, vid))

    def remove_favorite(self, account_id, vid):
        if (account_id, vid) in self.favs:
            self.favs.remove((account_id, vid))

    # auditoria
    def add_audit(self, vid, action):
        a = VentureAudit(venture_id=vid, action=action)
        a.id = self._next("a")
        a.timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.audit_rows.append(a)

    def audits(self, vid):
        return [a for a in self.audit_rows if a.venture_id == vid]
