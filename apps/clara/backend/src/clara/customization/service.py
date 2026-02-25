import uuid
from collections.abc import Sequence

from clara.customization.models import (
    CustomFieldDefinition,
    CustomFieldValue,
    Template,
    TemplateModule,
    TemplatePage,
)
from clara.customization.repository import (
    CustomFieldDefinitionRepository,
    CustomFieldValueRepository,
    TemplateModuleRepository,
    TemplatePageRepository,
    TemplateRepository,
)
from clara.customization.schemas import (
    CustomFieldDefinitionCreate,
    CustomFieldDefinitionUpdate,
    CustomFieldValueSet,
    TemplateCreate,
    TemplateUpdate,
)
from clara.exceptions import NotFoundError


class TemplateService:
    def __init__(
        self,
        repo: TemplateRepository,
        page_repo: TemplatePageRepository,
        module_repo: TemplateModuleRepository,
    ) -> None:
        self.repo = repo
        self.page_repo = page_repo
        self.module_repo = module_repo

    async def list_templates(
        self, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Template], int]:
        return await self.repo.list_with_pages(offset=offset, limit=limit)

    async def get_template(self, template_id: uuid.UUID) -> Template:
        template = await self.repo.get_by_id_with_pages(template_id)
        if template is None:
            raise NotFoundError("Template", template_id)
        return template

    async def create_template(self, data: TemplateCreate) -> Template:
        template = await self.repo.create(
            name=data.name, description=data.description
        )
        for page_data in data.pages:
            page = await self.page_repo.create(
                template_id=template.id,
                slug=page_data.slug,
                name=page_data.name,
                order=page_data.order,
            )
            for mod_data in page_data.modules:
                await self.module_repo.create(
                    page_id=page.id,
                    module_type=mod_data.module_type,
                    order=mod_data.order,
                    config_json=mod_data.config_json,
                )
        return await self.get_template(template.id)

    async def update_template(
        self, template_id: uuid.UUID, data: TemplateUpdate
    ) -> Template:
        await self.repo.update(
            template_id, **data.model_dump(exclude_unset=True)
        )
        return await self.get_template(template_id)

    async def delete_template(self, template_id: uuid.UUID) -> None:
        await self.repo.soft_delete(template_id)

    async def add_page(
        self, template_id: uuid.UUID, slug: str, name: str, order: int = 0
    ) -> TemplatePage:
        await self.get_template(template_id)
        return await self.page_repo.create(
            template_id=template_id, slug=slug, name=name, order=order
        )

    async def update_page(
        self, page_id: uuid.UUID, **kwargs: object
    ) -> TemplatePage:
        return await self.page_repo.update(page_id, **kwargs)

    async def delete_page(self, page_id: uuid.UUID) -> None:
        await self.page_repo.soft_delete(page_id)

    async def add_module(
        self,
        page_id: uuid.UUID,
        module_type: str,
        order: int = 0,
        config_json: str | None = None,
    ) -> TemplateModule:
        return await self.module_repo.create(
            page_id=page_id,
            module_type=module_type,
            order=order,
            config_json=config_json,
        )

    async def update_module(
        self, module_id: uuid.UUID, **kwargs: object
    ) -> TemplateModule:
        return await self.module_repo.update(module_id, **kwargs)

    async def delete_module(self, module_id: uuid.UUID) -> None:
        await self.module_repo.soft_delete(module_id)


class CustomFieldService:
    def __init__(
        self,
        def_repo: CustomFieldDefinitionRepository,
        val_repo: CustomFieldValueRepository,
    ) -> None:
        self.def_repo = def_repo
        self.val_repo = val_repo

    async def list_definitions(
        self, *, scope: str | None = None, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[CustomFieldDefinition], int]:
        if scope:
            return await self.def_repo.list_by_scope(
                scope, offset=offset, limit=limit
            )
        return await self.def_repo.list(offset=offset, limit=limit)

    async def get_definition(
        self, definition_id: uuid.UUID
    ) -> CustomFieldDefinition:
        defn = await self.def_repo.get_by_id(definition_id)
        if defn is None:
            raise NotFoundError("CustomFieldDefinition", definition_id)
        return defn

    async def create_definition(
        self, data: CustomFieldDefinitionCreate
    ) -> CustomFieldDefinition:
        return await self.def_repo.create(**data.model_dump())

    async def update_definition(
        self, definition_id: uuid.UUID, data: CustomFieldDefinitionUpdate
    ) -> CustomFieldDefinition:
        return await self.def_repo.update(
            definition_id, **data.model_dump(exclude_unset=True)
        )

    async def delete_definition(self, definition_id: uuid.UUID) -> None:
        await self.def_repo.soft_delete(definition_id)

    async def get_values_for_entity(
        self, entity_type: str, entity_id: uuid.UUID
    ) -> list[CustomFieldValue]:
        return await self.val_repo.list_for_entity(entity_type, entity_id)

    async def set_value(self, data: CustomFieldValueSet) -> CustomFieldValue:
        existing = await self.val_repo.get_by_definition_and_entity(
            data.definition_id, data.entity_type, data.entity_id
        )
        if existing:
            return await self.val_repo.update(
                existing.id, value_json=data.value_json
            )
        return await self.val_repo.create(**data.model_dump())

    async def delete_value(self, value_id: uuid.UUID) -> None:
        await self.val_repo.soft_delete(value_id)
