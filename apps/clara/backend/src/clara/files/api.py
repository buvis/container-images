import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import Response

from clara.base.schema import PaginatedResponse, PaginationMeta
from clara.deps import CurrentUser, Db, VaultAccess
from clara.files.repository import FileLinkRepository, FileRepository
from clara.files.schemas import FileLinkCreate, FileLinkRead, FileRead, FileUpdate
from clara.files.service import FileService
from clara.files.storage import LocalStorage
from clara.pagination import PaginationParams

router = APIRouter()


def get_file_service(
    vault_id: uuid.UUID,
    db: Db,
    _access: VaultAccess,
    user: CurrentUser,
) -> FileService:
    repo = FileRepository(session=db, vault_id=vault_id)
    link_repo = FileLinkRepository(session=db, vault_id=vault_id)
    storage = LocalStorage()
    return FileService(
        repo=repo,
        link_repo=link_repo,
        storage=storage,
        uploader_id=user.id,
    )


FileSvc = Annotated[FileService, Depends(get_file_service)]


@router.get("", response_model=PaginatedResponse[FileRead])
async def list_files(
    svc: FileSvc,
    pagination: PaginationParams = Depends(),
    q: str | None = None,
) -> PaginatedResponse[FileRead]:
    items, total = await svc.list_files(
        offset=pagination.offset, limit=pagination.limit, q=q
    )
    return PaginatedResponse(
        items=[FileRead.model_validate(f) for f in items],
        meta=PaginationMeta(
            total=total, offset=pagination.offset, limit=pagination.limit
        ),
    )


@router.post("", response_model=FileRead, status_code=201)
async def upload_file(file: UploadFile, svc: FileSvc) -> FileRead:
    return FileRead.model_validate(await svc.upload_file(file))


@router.get("/{file_id}", response_model=FileRead)
async def get_file(file_id: uuid.UUID, svc: FileSvc) -> FileRead:
    return FileRead.model_validate(await svc.get_file(file_id))


@router.get("/{file_id}/download")
async def download_file(file_id: uuid.UUID, svc: FileSvc) -> Response:
    data, file = await svc.download_file(file_id)
    return Response(
        content=data,
        media_type=file.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{file.filename}"'
        },
    )


@router.delete("/{file_id}", status_code=204)
async def delete_file(file_id: uuid.UUID, svc: FileSvc) -> None:
    await svc.delete_file(file_id)


@router.patch("/{file_id}", response_model=FileRead)
async def update_file(
    file_id: uuid.UUID, body: FileUpdate, svc: FileSvc
) -> FileRead:
    return FileRead.model_validate(
        await svc.update_file(file_id, **body.model_dump(exclude_unset=True))
    )


@router.post("/links", response_model=FileLinkRead, status_code=201)
async def create_file_link(body: FileLinkCreate, svc: FileSvc) -> FileLinkRead:
    return FileLinkRead.model_validate(await svc.create_link(body))


@router.get(
    "/links/by-target/{target_type}/{target_id}",
    response_model=list[FileLinkRead],
)
async def list_file_links_for_target(
    target_type: str, target_id: uuid.UUID, svc: FileSvc
) -> list[FileLinkRead]:
    return [
        FileLinkRead.model_validate(link)
        for link in await svc.list_links_for_target(target_type, target_id)
    ]


@router.delete("/links/{link_id}", status_code=204)
async def delete_file_link(link_id: uuid.UUID, svc: FileSvc) -> None:
    await svc.delete_link(link_id)
