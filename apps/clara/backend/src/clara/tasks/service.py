import uuid
from collections.abc import Sequence
from datetime import date

from clara.exceptions import NotFoundError
from clara.tasks.models import Task
from clara.tasks.repository import TaskRepository
from clara.tasks.schemas import TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, repo: TaskRepository, user_id: uuid.UUID) -> None:
        self.repo = repo
        self.user_id = user_id

    async def list_tasks(
        self, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Task], int]:
        return await self.repo.list(offset=offset, limit=limit)

    async def list_by_status(
        self, status: str, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Task], int]:
        return await self.repo.list_by_status(status, offset=offset, limit=limit)

    async def list_by_due_date_range(
        self, start: date, end: date, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Task], int]:
        return await self.repo.list_by_due_date_range(
            start, end, offset=offset, limit=limit
        )

    async def list_overdue(
        self, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Task], int]:
        return await self.repo.list_overdue(offset=offset, limit=limit)

    async def get_task(self, task_id: uuid.UUID) -> Task:
        task = await self.repo.get_by_id(task_id)
        if task is None:
            raise NotFoundError("Task", task_id)
        return task

    async def create_task(self, data: TaskCreate) -> Task:
        return await self.repo.create(
            **data.model_dump(), created_by_id=self.user_id
        )

    async def update_task(self, task_id: uuid.UUID, data: TaskUpdate) -> Task:
        return await self.repo.update(
            task_id, **data.model_dump(exclude_unset=True)
        )

    async def delete_task(self, task_id: uuid.UUID) -> None:
        await self.repo.soft_delete(task_id)
