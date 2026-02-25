from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    total: int
    offset: int
    limit: int


class PaginatedResponse[T](BaseModel):
    items: list[T]
    meta: PaginationMeta
