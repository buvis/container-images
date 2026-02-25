import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from clara.base.schema import PaginatedResponse, PaginationMeta
from clara.customization.repository import (
    TemplateModuleRepository,
    TemplatePageRepository,
    TemplateRepository,
)
from clara.customization.schemas import (
    TemplateCreate,
    TemplateModuleCreate,
    TemplateModuleRead,
    TemplateModuleUpdate,
    TemplatePageCreate,
    TemplatePageRead,
    TemplatePageUpdate,
    TemplateRead,
    TemplateUpdate,
)
from clara.customization.service import TemplateService
from clara.deps import Db, VaultAccess
from clara.pagination import PaginationParams

router = APIRouter()


def get_template_service(
    vault_id: uuid.UUID, db: Db, _access: VaultAccess
) -> TemplateService:
    repo = TemplateRepository(session=db, vault_id=vault_id)
    page_repo = TemplatePageRepository(session=db, vault_id=vault_id)
    module_repo = TemplateModuleRepository(session=db, vault_id=vault_id)
    return TemplateService(
        repo=repo, page_repo=page_repo, module_repo=module_repo
    )


TplSvc = Annotated[TemplateService, Depends(get_template_service)]


@router.get("", response_model=PaginatedResponse[TemplateRead])
async def list_templates(
    svc: TplSvc, pagination: PaginationParams = Depends()
) -> PaginatedResponse[TemplateRead]:
    items, total = await svc.list_templates(
        offset=pagination.offset, limit=pagination.limit
    )
    return PaginatedResponse(
        items=[TemplateRead.model_validate(t) for t in items],
        meta=PaginationMeta(
            total=total, offset=pagination.offset, limit=pagination.limit
        ),
    )


@router.post("", response_model=TemplateRead, status_code=201)
async def create_template(body: TemplateCreate, svc: TplSvc) -> TemplateRead:
    return TemplateRead.model_validate(await svc.create_template(body))


@router.get("/{template_id}", response_model=TemplateRead)
async def get_template(template_id: uuid.UUID, svc: TplSvc) -> TemplateRead:
    return TemplateRead.model_validate(await svc.get_template(template_id))


@router.patch("/{template_id}", response_model=TemplateRead)
async def update_template(
    template_id: uuid.UUID, body: TemplateUpdate, svc: TplSvc
) -> TemplateRead:
    return TemplateRead.model_validate(
        await svc.update_template(template_id, body)
    )


@router.delete("/{template_id}", status_code=204)
async def delete_template(template_id: uuid.UUID, svc: TplSvc) -> None:
    await svc.delete_template(template_id)


@router.post(
    "/{template_id}/pages", response_model=TemplatePageRead, status_code=201
)
async def add_page(
    template_id: uuid.UUID, body: TemplatePageCreate, svc: TplSvc
) -> TemplatePageRead:
    page = await svc.add_page(
        template_id, slug=body.slug, name=body.name, order=body.order
    )
    for mod_data in body.modules:
        await svc.add_module(
            page.id,
            module_type=mod_data.module_type,
            order=mod_data.order,
            config_json=mod_data.config_json,
        )
    template = await svc.get_template(template_id)
    for p in template.pages:
        if p.id == page.id:
            return TemplatePageRead.model_validate(p)
    return TemplatePageRead.model_validate(page)


@router.patch("/pages/{page_id}", response_model=TemplatePageRead)
async def update_page(
    page_id: uuid.UUID, body: TemplatePageUpdate, svc: TplSvc
) -> TemplatePageRead:
    page = await svc.update_page(
        page_id, **body.model_dump(exclude_unset=True)
    )
    return TemplatePageRead.model_validate(page)


@router.delete("/pages/{page_id}", status_code=204)
async def delete_page(page_id: uuid.UUID, svc: TplSvc) -> None:
    await svc.delete_page(page_id)


@router.post(
    "/pages/{page_id}/modules",
    response_model=TemplateModuleRead,
    status_code=201,
)
async def add_module(
    page_id: uuid.UUID, body: TemplateModuleCreate, svc: TplSvc
) -> TemplateModuleRead:
    module = await svc.add_module(
        page_id,
        module_type=body.module_type,
        order=body.order,
        config_json=body.config_json,
    )
    return TemplateModuleRead.model_validate(module)


@router.patch("/modules/{module_id}", response_model=TemplateModuleRead)
async def update_module(
    module_id: uuid.UUID, body: TemplateModuleUpdate, svc: TplSvc
) -> TemplateModuleRead:
    module = await svc.update_module(
        module_id, **body.model_dump(exclude_unset=True)
    )
    return TemplateModuleRead.model_validate(module)


@router.delete("/modules/{module_id}", status_code=204)
async def delete_module(module_id: uuid.UUID, svc: TplSvc) -> None:
    await svc.delete_module(module_id)
