from collections.abc import Sequence
from datetime import date

from clara.base.repository import BaseRepository
from clara.tasks.models import Task


class TaskRepository(BaseRepository[Task]):
    model = Task

    async def list_by_status(
        self, status: str, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Task], int]:
        return await self.filtered_list(
            Task.status == status, offset=offset, limit=limit
        )

    async def list_by_due_date_range(
        self, start: date, end: date, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Task], int]:
        return await self.filtered_list(
            Task.due_date >= start,
            Task.due_date <= end,
            order_by=Task.due_date.asc(),
            offset=offset,
            limit=limit,
        )

    async def list_overdue(
        self, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Task], int]:
        today = date.today()
        return await self.filtered_list(
            Task.due_date < today,
            Task.status != "done",
            order_by=Task.due_date.asc(),
            offset=offset,
            limit=limit,
        )
