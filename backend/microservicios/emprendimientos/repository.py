"""Acceso a datos del servicio de emprendimientos (patron Repository).

Es la unica capa que conoce SQL/SQLModel.
"""
from typing import Optional

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from models import (
    Category,
    Favorite,
    FollowerStat,
    SocialLink,
    Venture,
    VentureAudit,
)


class DuplicateVenture(Exception):
    """La cuenta ya tiene un emprendimiento (restriccion unica en la BD)."""


class VentureRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def commit(self) -> None:
        self.session.commit()

    def save(self, obj) -> None:
        self.session.add(obj)

    # ---- categorias ----
    def categories(self, only_active: bool = True) -> list[Category]:
        stmt = select(Category)
        if only_active:
            stmt = stmt.where(Category.is_active == True)  # noqa: E712
        return list(self.session.exec(stmt.order_by(Category.id)).all())

    def get_category(self, category_id: int) -> Optional[Category]:
        return self.session.get(Category, category_id)

    def count_categories(self) -> int:
        return self.session.exec(select(func.count()).select_from(Category)).one()

    def add_category(self, name: str) -> Category:
        cat = Category(name=name)
        self.session.add(cat)
        self.session.flush()
        return cat

    # ---- emprendimientos ----
    def get_venture(self, venture_id: int) -> Optional[Venture]:
        return self.session.get(Venture, venture_id)

    def get_by_owner(self, account_id: int) -> Optional[Venture]:
        return self.session.exec(
            select(Venture).where(Venture.owner_account_id == account_id)
        ).first()

    def add_venture(self, venture: Venture) -> Venture:
        self.session.add(venture)
        try:
            self.session.flush()
        except IntegrityError as exc:
            self.session.rollback()
            raise DuplicateVenture() from exc
        return venture

    def search_public(
        self, q: Optional[str], category_id: Optional[int], limit: int, offset: int
    ) -> tuple[list[Venture], int]:
        """Solo publicados y activos, los mas nuevos primero."""
        conds = [Venture.is_published == True, Venture.is_active == True]  # noqa: E712
        if category_id is not None:
            conds.append(Venture.category_id == category_id)
        if q:
            like = f"%{q.lower()}%"
            conds.append(
                func.lower(Venture.name).like(like)
                | func.lower(func.coalesce(Venture.description, "")).like(like)
            )
        total = self.session.exec(select(func.count()).select_from(Venture).where(*conds)).one()
        rows = self.session.exec(
            select(Venture).where(*conds).order_by(Venture.id.desc()).offset(offset).limit(limit)
        ).all()
        return list(rows), total

    def public_by_ids(self, ids: list[int]) -> list[Venture]:
        if not ids:
            return []
        rows = self.session.exec(
            select(Venture).where(
                Venture.id.in_(ids),
                Venture.is_published == True,  # noqa: E712
                Venture.is_active == True,  # noqa: E712
            )
        ).all()
        return list(rows)

    # ---- redes del negocio ----
    def links_for(self, venture_ids: list[int]) -> list[SocialLink]:
        if not venture_ids:
            return []
        return list(
            self.session.exec(
                select(SocialLink)
                .where(SocialLink.venture_id.in_(venture_ids), SocialLink.is_active == True)  # noqa: E712
                .order_by(SocialLink.id)
            ).all()
        )

    def get_link(self, venture_id: int, platform: str) -> Optional[SocialLink]:
        return self.session.exec(
            select(SocialLink)
            .where(SocialLink.venture_id == venture_id)
            .where(SocialLink.platform == platform)
        ).first()

    def add_link(self, link: SocialLink) -> SocialLink:
        self.session.add(link)
        self.session.flush()
        return link

    def latest_stats(self, link_ids: list[int]) -> dict[int, FollowerStat]:
        """Ultimo dato de seguidores de cada red."""
        if not link_ids:
            return {}
        rows = self.session.exec(
            select(FollowerStat)
            .where(FollowerStat.social_link_id.in_(link_ids))
            .order_by(FollowerStat.id)
        ).all()
        return {row.social_link_id: row for row in rows}  # el ultimo gana

    def stat_history(self, link_ids: list[int]) -> list[FollowerStat]:
        if not link_ids:
            return []
        return list(
            self.session.exec(
                select(FollowerStat)
                .where(FollowerStat.social_link_id.in_(link_ids))
                .order_by(FollowerStat.id.desc())
            ).all()
        )

    def add_stat(self, stat: FollowerStat) -> None:
        self.session.add(stat)

    # ---- favoritos ----
    def favorite_ids(self, account_id: int) -> list[int]:
        rows = self.session.exec(
            select(Favorite.venture_id)
            .where(Favorite.account_id == account_id)
            .order_by(Favorite.created_at.desc())
        ).all()
        return list(rows)

    def has_favorite(self, account_id: int, venture_id: int) -> bool:
        return self.session.get(Favorite, (account_id, venture_id)) is not None

    def add_favorite(self, account_id: int, venture_id: int) -> None:
        self.session.add(Favorite(account_id=account_id, venture_id=venture_id))
        self.session.flush()

    def remove_favorite(self, account_id: int, venture_id: int) -> None:
        fav = self.session.get(Favorite, (account_id, venture_id))
        if fav is not None:
            self.session.delete(fav)

    # ---- auditoria ----
    def add_audit(self, venture_id: int, action: str) -> None:
        self.session.add(VentureAudit(venture_id=venture_id, action=action))

    def audits(self, venture_id: int) -> list[VentureAudit]:
        return list(
            self.session.exec(
                select(VentureAudit)
                .where(VentureAudit.venture_id == venture_id)
                .order_by(VentureAudit.id)
            ).all()
        )
