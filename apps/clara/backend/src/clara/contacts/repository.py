import uuid
from collections.abc import Sequence
from datetime import date
from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import selectinload

from clara.base.repository import BaseRepository
from clara.contacts.models import (
    Address,
    Contact,
    ContactMethod,
    ContactRelationship,
    Pet,
    RelationshipType,
    Tag,
    contact_tags,
)


class ContactRepository(BaseRepository[Contact]):
    model = Contact

    def _base_query(self) -> Select[tuple[Contact]]:
        return super()._base_query().options(
            selectinload(Contact.contact_methods),
            selectinload(Contact.addresses),
            selectinload(Contact.tags),
            selectinload(Contact.pets),
            selectinload(Contact.relationships),
        )

    def _apply_filters(
        self,
        stmt: Select[Any],
        *,
        q: str | None = None,
        tag_ids: list[uuid.UUID] | None = None,
        favorites: bool | None = None,
        birthday_from: date | None = None,
        birthday_to: date | None = None,
    ) -> Select[Any]:
        if q:
            pattern = f"%{q}%"
            stmt = stmt.where(
                or_(
                    Contact.first_name.ilike(pattern),
                    Contact.last_name.ilike(pattern),
                    Contact.nickname.ilike(pattern),
                )
            )
        if tag_ids:
            stmt = stmt.join(
                contact_tags, contact_tags.c.contact_id == Contact.id
            ).where(contact_tags.c.tag_id.in_(tag_ids))
        if favorites is not None:
            stmt = stmt.where(Contact.favorite.is_(favorites))
        if birthday_from is not None:
            stmt = stmt.where(Contact.birthdate >= birthday_from)
        if birthday_to is not None:
            stmt = stmt.where(Contact.birthdate <= birthday_to)
        return stmt

    async def list_filtered(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        q: str | None = None,
        tag_ids: list[uuid.UUID] | None = None,
        favorites: bool | None = None,
        birthday_from: date | None = None,
        birthday_to: date | None = None,
    ) -> tuple[Sequence[Contact], int]:
        count_stmt = self._apply_filters(
            select(func.count(func.distinct(self.model.id)))
            .select_from(self.model)
            .where(self.model.vault_id == self.vault_id)
            .where(self.model.deleted_at.is_(None)),
            q=q, tag_ids=tag_ids, favorites=favorites,
            birthday_from=birthday_from, birthday_to=birthday_to,
        )
        total: int = (await self.session.execute(count_stmt)).scalar_one()
        items_stmt = self._apply_filters(
            self._base_query(),
            q=q, tag_ids=tag_ids, favorites=favorites,
            birthday_from=birthday_from, birthday_to=birthday_to,
        )
        if tag_ids:
            items_stmt = items_stmt.distinct()
        items_stmt = (
            items_stmt.offset(offset)
            .limit(limit)
            .order_by(Contact.created_at.desc())
        )
        result = await self.session.execute(items_stmt)
        return result.scalars().all(), total

    async def search(
        self, query: str, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Contact], int]:
        return await self.list_filtered(q=query, offset=offset, limit=limit)


class ContactMethodRepository(BaseRepository[ContactMethod]):
    model = ContactMethod

    async def list_for_contact(self, contact_id: uuid.UUID) -> list[ContactMethod]:
        stmt = (
            self._base_query()
            .where(ContactMethod.contact_id == contact_id)
            .order_by(ContactMethod.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_for_contact(
        self, contact_id: uuid.UUID, method_id: uuid.UUID
    ) -> ContactMethod | None:
        stmt = self._base_query().where(
            ContactMethod.contact_id == contact_id,
            ContactMethod.id == method_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class AddressRepository(BaseRepository[Address]):
    model = Address

    async def list_for_contact(self, contact_id: uuid.UUID) -> list[Address]:
        stmt = (
            self._base_query()
            .where(Address.contact_id == contact_id)
            .order_by(Address.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_for_contact(
        self, contact_id: uuid.UUID, address_id: uuid.UUID
    ) -> Address | None:
        stmt = self._base_query().where(
            Address.contact_id == contact_id,
            Address.id == address_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class RelationshipRepository(BaseRepository[ContactRelationship]):
    model = ContactRelationship

    async def list_for_contact(
        self, contact_id: uuid.UUID
    ) -> list[ContactRelationship]:
        stmt = (
            self._base_query()
            .where(ContactRelationship.contact_id == contact_id)
            .order_by(ContactRelationship.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_for_contact(
        self, contact_id: uuid.UUID, relationship_id: uuid.UUID
    ) -> ContactRelationship | None:
        stmt = self._base_query().where(
            ContactRelationship.contact_id == contact_id,
            ContactRelationship.id == relationship_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class PetRepository(BaseRepository[Pet]):
    model = Pet

    async def list_for_contact(self, contact_id: uuid.UUID) -> list[Pet]:
        stmt = (
            self._base_query()
            .where(Pet.contact_id == contact_id)
            .order_by(Pet.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_for_contact(
        self, contact_id: uuid.UUID, pet_id: uuid.UUID
    ) -> Pet | None:
        stmt = self._base_query().where(
            Pet.contact_id == contact_id,
            Pet.id == pet_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class TagRepository(BaseRepository[Tag]):
    model = Tag

    async def list_all(self) -> list[Tag]:
        stmt = self._base_query().order_by(Tag.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class RelationshipTypeRepository(BaseRepository[RelationshipType]):
    model = RelationshipType

    async def list_all(self) -> list[RelationshipType]:
        stmt = self._base_query().order_by(RelationshipType.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
