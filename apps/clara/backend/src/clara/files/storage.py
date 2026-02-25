import uuid
from pathlib import Path

import aiofiles

from clara.config import get_settings


class LocalStorage:
    def __init__(self) -> None:
        self.base_path = Path(get_settings().storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save(self, data: bytes, filename: str) -> str:
        key = f"{uuid.uuid4()}/{filename}"
        path = self.base_path / key
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "wb") as f:
            await f.write(data)
        return key

    async def read(self, key: str) -> bytes:
        path = self.base_path / key
        async with aiofiles.open(path, "rb") as f:
            data: bytes = await f.read()
            return data

    async def delete(self, key: str) -> None:
        path = self.base_path / key
        path.unlink(missing_ok=True)
