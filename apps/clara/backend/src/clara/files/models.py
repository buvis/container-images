import uuid

from sqlalchemy import BigInteger, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from clara.base.model import VaultScopedModel


class File(VaultScopedModel):
    __tablename__ = "files"
    uploader_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id")
    )
    storage_key: Mapped[str] = mapped_column(String(1000))
    filename: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str] = mapped_column(String(200))
    size_bytes: Mapped[int] = mapped_column(BigInteger)


class FileLink(VaultScopedModel):
    __tablename__ = "file_links"
    file_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("files.id")
    )
    target_type: Mapped[str] = mapped_column(String(50))
    target_id: Mapped[uuid.UUID] = mapped_column(Uuid)
