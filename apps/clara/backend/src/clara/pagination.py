from dataclasses import dataclass

from fastapi import Query


@dataclass
class PaginationParams:
    offset: int = Query(0, ge=0)
    limit: int = Query(50, ge=1, le=200)
