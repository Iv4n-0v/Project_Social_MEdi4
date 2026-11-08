"""Logica de negocio del servicio de emprendimientos.

No conoce HTTP (los errores son clases con nombre; main.py las traduce) ni SQL
(eso es del repositorio). La identidad (account_id) siempre llega ya validada
por el gateway; el servicio nunca la recibe del cuerpo de la peticion.
"""
import datetime
import urllib.parse
from typing import Optional

from models import Category, FollowerStat, SocialLink, Venture, utcnow
from repository import DuplicateVenture
from schemas import (
    CategoryResponse,
    OwnVenture,
    PublicVenture,
    PublicVentureList,
    SocialPublic,
    VentureSave,
)

# Lista base. Se siembra solo si la tabla esta vacia; luego se puede ajustar en la BD.
DEFAULT_CATEGORIES = [
    "Moda y accesorios",
    "Alimentos y bebidas",
    "Belleza y cuidado personal",
    "Tecnología",
    "Arte y manualidades",
    "Educación y formación",
    "Servicios profesionales",
    "Hogar y decoración",
    "Salud y bienestar",
    "Entretenimiento y eventos",
    "Otros",
]

# Redes del negocio permitidas y los dominios validos de su enlace.
PLATFORMS = {
    "instagram": ("instagram.com",),
    "facebook": ("facebook.com", "fb.com", "fb.me"),
    "tiktok": ("tiktok.com",),
    "whatsapp": ("wa.me", "whatsapp.com"),
    "youtube": ("youtube.com", "youtu.be"),
}

MAX_PAGE = 50


# ---- errores de dominio ----
class VentureError(Exception):
    pass


class InvalidInput(VentureError):
    pass


class VentureNotFound(VentureError):
    pass


class VentureInactive(VentureError):
    pass


class NotPublishable(VentureError):
    pass


def seed_categories(repo) -> None:
    if repo.count_categories() == 0:
        for name in DEFAULT_CATEGORIES:
            repo.add_category(name)
        repo.commit()


def _clean(value: Optional[str]) -> Optional[str]:
    value = (value or "").strip()
    return value or None


def validate_social_url(platform: str, url: str) -> str:
    """Solo https/http y solo el dominio de esa red (evita enlaces a otros sitios)."""
    if platform not in PLATFORMS:
        raise InvalidInput(f"Red no valida. Opciones: {', '.join(PLATFORMS)}")
    url = (url or "").strip()
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ("http", "https") or not host:
        raise InvalidInput("El enlace debe empezar por https://")
    if not any(host == d or host.endswith("." + d) for d in PLATFORMS[platform]):
        raise InvalidInput(f"El enlace no corresponde a {platform}")
    return url


class VentureService:
    def __init__(self, repo, clock=None) -> None:
        self.repo = repo
        self._clock = clock

    def _now(self) -> datetime.datetime:
        return self._clock() if self._clock else utcnow()

    # ---- armado de respuestas ----
    def _social_map(self, venture_ids: list[int]) -> dict:
        links = self.repo.links_for(venture_ids)
        stats = self.repo.latest_stats([l.id for l in links])
        out: dict = {}
        for link in links:
            stat = stats.get(link.id)
            out.setdefault(link.venture_id, []).append(
                SocialPublic(
                    platform=link.platform,
                    url=link.url,
                    followers=stat.followers if stat else None,
                    followers_source=stat.source if stat else None,
                    followers_updated_at=stat.updated_at if stat else None,
                )
            )
        return out

    def _category(self, category_id: Optional[int]) -> Optional[CategoryResponse]:
        if category_id is None:
            return None
        cat = self.repo.get_category(category_id)
        return CategoryResponse(id=cat.id, name=cat.name) if cat else None

    def _public(self, v: Venture, socials: dict) -> PublicVenture:
        return PublicVenture(
            id=v.id,
            name=v.name,
            # El nombre del emprendedor solo sale si el decidio publicarlo
            entrepreneur_name=v.entrepreneur_name if v.show_entrepreneur_name else None,
            description=v.description,
            location=v.location,
            category=self._category(v.category_id),
            profile_image_url=v.profile_image_url,
            social=socials.get(v.id, []),
        )

    def _public_list(self, ventures: list[Venture]) -> list[PublicVenture]:
        socials = self._social_map([v.id for v in ventures])
        return [self._public(v, socials) for v in ventures]

    def _own(self, v: Venture) -> OwnVenture:
        base = self._public(v, self._social_map([v.id]))
        data = base.model_dump()
        data["entrepreneur_name"] = v.entrepreneur_name
        return OwnVenture(
            **data,
            show_entrepreneur_name=v.show_entrepreneur_name,
            is_published=v.is_published,
            is_active=v.is_active,
            category_id=v.category_id,
            created_at=v.created_at,
            updated_at=v.updated_at,
        )

    # ---- publico ----
    def list_categories(self) -> list[CategoryResponse]:
        return [CategoryResponse(id=c.id, name=c.name) for c in self.repo.categories()]

    def search(
        self, q: Optional[str], category_id: Optional[int], limit: int, offset: int
    ) -> PublicVentureList:
        limit = max(1, min(limit, MAX_PAGE))
        offset = max(0, offset)
        q = _clean(q)
        if q and len(q) > 100:
            q = q[:100]
        rows, total = self.repo.search_public(q, category_id, limit, offset)
        return PublicVentureList(items=self._public_list(rows), total=total, limit=limit, offset=offset)

    def get_public(self, venture_id: int) -> PublicVenture:
        v = self.repo.get_venture(venture_id)
        # Un borrador o un emprendimiento eliminado "no existe" para el visitante
        if v is None or not v.is_published or not v.is_active:
            raise VentureNotFound("Emprendimiento no encontrado")
        return self._public_list([v])[0]

    # ---- emprendimiento propio ----
    def _mine(self, account_id: int) -> Venture:
        v = self.repo.get_by_owner(account_id)
        if v is None:
            raise VentureNotFound("Aun no has creado tu emprendimiento")
        return v

    def _active_mine(self, account_id: int) -> Venture:
        v = self._mine(account_id)
        if not v.is_active:
            raise VentureInactive("Tu emprendimiento esta eliminado. Restauralo primero")
        return v

    def get_mine(self, account_id: int) -> OwnVenture:
        return self._own(self._mine(account_id))

    def _check_category(self, category_id: Optional[int]) -> None:
        if category_id is not None:
            cat = self.repo.get_category(category_id)
            if cat is None or not cat.is_active:
                raise InvalidInput("La categoria no existe")

    def save_mine(self, account_id: int, data: VentureSave) -> tuple[OwnVenture, bool]:
        """Crea el emprendimiento (como borrador) o actualiza el existente.

        Devuelve (emprendimiento, fue_creado).
        """
        self._check_category(data.category_id)
        fields = dict(
            name=data.name.strip(),
            entrepreneur_name=_clean(data.entrepreneur_name),
            show_entrepreneur_name=data.show_entrepreneur_name,
            description=_clean(data.description),
            location=_clean(data.location),
            category_id=data.category_id,
        )
        if not fields["name"]:
            raise InvalidInput("El nombre es obligatorio")
        existing = self.repo.get_by_owner(account_id)
        if existing is None:
            try:
                v = self.repo.add_venture(Venture(owner_account_id=account_id, **fields))
            except DuplicateVenture:  # dos peticiones a la vez: la otra ya lo creo
                raise InvalidInput("Ya existe un emprendimiento para esta cuenta")
            self.repo.add_audit(v.id, "CREATE")
            created = True
        else:
            if not existing.is_active:
                raise VentureInactive("Tu emprendimiento esta eliminado. Restauralo primero")
            v = existing
            for key, value in fields.items():
                setattr(v, key, value)
            v.updated_at = self._now()
            self.repo.save(v)
            self.repo.add_audit(v.id, "UPDATE")
            created = False
        self.repo.commit()
        return self._own(v), created

    def publish(self, account_id: int) -> OwnVenture:
        v = self._active_mine(account_id)
        missing = []
        if not _clean(v.name):
            missing.append("nombre")
        if not _clean(v.description):
            missing.append("descripcion")
        if missing:
            raise NotPublishable("Para publicar completa: " + ", ".join(missing))
        if not v.is_published:
            v.is_published = True
            v.updated_at = self._now()
            self.repo.save(v)
            self.repo.add_audit(v.id, "PUBLISH")
            self.repo.commit()
        return self._own(v)

    def unpublish(self, account_id: int) -> OwnVenture:
        v = self._active_mine(account_id)
        if v.is_published:
            v.is_published = False
            v.updated_at = self._now()
            self.repo.save(v)
            self.repo.add_audit(v.id, "UNPUBLISH")
            self.repo.commit()
        return self._own(v)

    def delete_mine(self, account_id: int) -> OwnVenture:
        """Borrado logico: deja de verse y puede restaurarse (como borrador)."""
        v = self._mine(account_id)
        if v.is_active:
            v.is_active = False
            v.is_published = False
            v.updated_at = self._now()
            self.repo.save(v)
            self.repo.add_audit(v.id, "DELETE")
            self.repo.commit()
        return self._own(v)

    def restore_mine(self, account_id: int) -> OwnVenture:
        v = self._mine(account_id)
        if not v.is_active:
            v.is_active = True
            v.updated_at = self._now()
            self.repo.save(v)
            self.repo.add_audit(v.id, "RESTORE")
            self.repo.commit()
        return self._own(v)

    def audits_mine(self, account_id: int) -> list:
        return self.repo.audits(self._mine(account_id).id)

    # ---- redes del negocio ----
    def set_social(
        self, account_id: int, platform: str, url: str, followers: Optional[int]
    ) -> OwnVenture:
        v = self._active_mine(account_id)
        url = validate_social_url(platform, url)
        link = self.repo.get_link(v.id, platform)
        if link is None:
            link = self.repo.add_link(SocialLink(venture_id=v.id, platform=platform, url=url))
        else:
            link.url = url
            link.is_active = True
            self.repo.save(link)
        if followers is not None:
            self.repo.add_stat(
                FollowerStat(social_link_id=link.id, followers=followers, source="manual", updated_at=self._now())
            )
        self.repo.add_audit(v.id, f"SOCIAL_SET:{platform}")
        self.repo.commit()
        return self._own(v)

    def remove_social(self, account_id: int, platform: str) -> OwnVenture:
        v = self._active_mine(account_id)
        if platform not in PLATFORMS:
            raise InvalidInput("Red no valida")
        link = self.repo.get_link(v.id, platform)
        if link is not None and link.is_active:
            link.is_active = False  # borrado logico: la red y su historial se conservan
            self.repo.save(link)
            self.repo.add_audit(v.id, f"SOCIAL_REMOVE:{platform}")
            self.repo.commit()
        return self._own(v)

    # ---- favoritos (privados por cuenta) ----
    def favorite_ids(self, account_id: int) -> list[int]:
        return self.repo.favorite_ids(account_id)

    def list_favorites(self, account_id: int) -> list[PublicVenture]:
        ids = self.repo.favorite_ids(account_id)
        by_id = {v.id: v for v in self.repo.public_by_ids(ids)}
        # conserva el orden "mas recientes primero" y omite los que ya no son publicos
        return self._public_list([by_id[i] for i in ids if i in by_id])

    def add_favorite(self, account_id: int, venture_id: int) -> None:
        v = self.repo.get_venture(venture_id)
        if v is None or not v.is_published or not v.is_active:
            raise VentureNotFound("Emprendimiento no encontrado")
        if not self.repo.has_favorite(account_id, venture_id):
            self.repo.add_favorite(account_id, venture_id)
            self.repo.commit()

    def remove_favorite(self, account_id: int, venture_id: int) -> None:
        self.repo.remove_favorite(account_id, venture_id)
        self.repo.commit()
