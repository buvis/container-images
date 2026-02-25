import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from clara.base.repository import BaseRepository
from clara.customization.models import (
    CustomFieldDefinition,
    CustomFieldValue,
    Template,
    TemplateModule,
    TemplatePage,
)


class TemplateRepository(BaseRepository[Template]):
    model = Template

    async def get_by_id_with_pages(
        self, template_id: uuid.UUID
    ) -> Template | None:
        stmt = (
            self._base_query()
            .where(Template.id == template_id)
            .options(
                selectinload(Template.pages).selectinload(
                    TemplatePage.modules
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_with_pages(
        self, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Template], int]:
        count_stmt = (
            select(func.count())
            .select_from(Template)
            .where(Template.vault_id == self.vault_id)
            .where(Template.deleted_at.is_(None))
        )
        total = (await self.session.execute(count_stmt)).scalar_one()
        items_stmt = (
            self._base_query()
            .options(
                selectinload(Template.pages).selectinload(
                    TemplatePage.modules
                )
            )
            .offset(offset)
            .limit(limit)
            .order_by(Template.created_at.desc())
        )
        result = await self.session.execute(items_stmt)
        return result.scalars().unique().all(), total


class TemplatePageRepository(BaseRepository[TemplatePage]):
    model = TemplatePage


class TemplateModuleRepository(BaseRepository[TemplateModule]):
    model = TemplateModule


class CustomFieldDefinitionRepository(BaseRepository[CustomFieldDefinition]):
    model = CustomFieldDefinition

    async def list_by_scope(
        self, scope: str, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[CustomFieldDefinition], int]:
        count_stmt = (
            select(func.count())
            .select_from(CustomFieldDefinition)
            .where(CustomFieldDefinition.vault_id == self.vault_id)
            .where(CustomFieldDefinition.deleted_at.is_(None))
            .where(CustomFieldDefinition.scope == scope)
        )
        total = (await self.session.execute(count_stmt)).scalar_one()
        items_stmt = (
            self._base_query()
            .where(CustomFieldDefinition.scope == scope)
            .offset(offset)
            .limit(limit)
            .order_by(CustomFieldDefinition.created_at.desc())
        )
        result = await self.session.execute(items_stmt)
        return result.scalars().all(), total


class CustomFieldValueRepository(BaseRepository[CustomFieldValue]):
    model = CustomFieldValue

    async def get_by_definition_and_entity(
        self,
        definition_id: uuid.UUID,
        entity_type: str,
        entity_id: uuid.UUID,
    ) -> CustomFieldValue | None:
        stmt = (
            self._base_query()
            .where(CustomFieldValue.definition_id == definition_id)
            .where(CustomFieldValue.entity_type == entity_type)
            .where(CustomFieldValue.entity_id == entity_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_entity(
        self, entity_type: str, entity_id: uuid.UUID
    ) -> list[CustomFieldValue]:
        stmt = (
            self._base_query()
            .where(CustomFieldValue.entity_type == entity_type)
            .where(CustomFieldValue.entity_id == entity_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
