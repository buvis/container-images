import uuid
from collections.abc import Sequence
from typing import Any

from fastapi import UploadFile

from clara.exceptions import NotFoundError
from clara.files.models import File, FileLink
from clara.files.repository import FileLinkRepository, FileRepository
from clara.files.schemas import FileLinkCreate
from clara.files.storage import LocalStorage


class FileService:
    def __init__(
        self,
        repo: FileRepository,
        link_repo: FileLinkRepository,
        storage: LocalStorage,
        uploader_id: uuid.UUID,
    ) -> None:
        self.repo = repo
        self.link_repo = link_repo
        self.storage = storage
        self.uploader_id = uploader_id

    async def list_files(
        self, *, offset: int = 0, limit: int = 50, q: str | None = None
    ) -> tuple[Sequence[File], int]:
        return await self.repo.list(offset=offset, limit=limit, q=q)

    async def get_file(self, file_id: uuid.UUID) -> File:
        file = await self.repo.get_by_id(file_id)
        if file is None:
            raise NotFoundError("File", file_id)
        return file

    async def upload_file(self, upload: UploadFile) -> File:
        data = await upload.read()
        filename = upload.filename or "unnamed"
        mime_type = upload.content_type or "application/octet-stream"
        storage_key = await self.storage.save(data, filename)
        return await self.repo.create(
            uploader_id=self.uploader_id,
            storage_key=storage_key,
            filename=filename,
            mime_type=mime_type,
            size_bytes=len(data),
        )

    async def download_file(self, file_id: uuid.UUID) -> tuple[bytes, File]:
        file = await self.get_file(file_id)
        data = await self.storage.read(file.storage_key)
        return data, file

    async def update_file(self, file_id: uuid.UUID, **kwargs: Any) -> File:
        return await self.repo.update(file_id, **kwargs)

    async def delete_file(self, file_id: uuid.UUID) -> None:
        file = await self.get_file(file_id)
        await self.storage.delete(file.storage_key)
        await self.repo.soft_delete(file_id)

    async def create_link(self, data: FileLinkCreate) -> FileLink:
        await self.get_file(data.file_id)
        return await self.link_repo.create(**data.model_dump())

    async def list_links_for_target(
        self, target_type: str, target_id: uuid.UUID
    ) -> list[FileLink]:
        return await self.link_repo.list_by_target(target_type, target_id)

    async def delete_link(self, link_id: uuid.UUID) -> None:
        await self.link_repo.soft_delete(link_id)
