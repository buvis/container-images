import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from clara.base.schema import PaginatedResponse, PaginationMeta
from clara.deps import CurrentUser, Db, VaultAccess
from clara.pagination import PaginationParams
from clara.tasks.repository import TaskRepository
from clara.tasks.schemas import TaskCreate, TaskRead, TaskUpdate
from clara.tasks.service import TaskService

router = APIRouter()


def get_task_service(
    vault_id: uuid.UUID, db: Db, _access: VaultAccess, user: CurrentUser
) -> TaskService:
    repo = TaskRepository(session=db, vault_id=vault_id)
    return TaskService(repo=repo, user_id=user.id)


TaskSvc = Annotated[TaskService, Depends(get_task_service)]


@router.get("", response_model=PaginatedResponse[TaskRead])
async def list_tasks(
    svc: TaskSvc,
    pagination: PaginationParams = Depends(),
    status: str | None = Query(None, description="Filter by status"),
    due_from: date | None = Query(None, description="Filter due_date >= this"),
    due_to: date | None = Query(None, description="Filter due_date <= this"),
    overdue: bool = Query(False, description="Only overdue tasks"),
) -> PaginatedResponse[TaskRead]:
    if overdue:
        items, total = await svc.list_overdue(
            offset=pagination.offset, limit=pagination.limit
        )
    elif status:
        items, total = await svc.list_by_status(
            status, offset=pagination.offset, limit=pagination.limit
        )
    elif due_from and due_to:
        items, total = await svc.list_by_due_date_range(
            due_from, due_to, offset=pagination.offset, limit=pagination.limit
        )
    else:
        items, total = await svc.list_tasks(
            offset=pagination.offset, limit=pagination.limit
        )
    return PaginatedResponse(
        items=[TaskRead.model_validate(t) for t in items],
        meta=PaginationMeta(
            total=total, offset=pagination.offset, limit=pagination.limit
        ),
    )


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(task_id: uuid.UUID, svc: TaskSvc) -> TaskRead:
    return TaskRead.model_validate(await svc.get_task(task_id))


@router.post("", response_model=TaskRead, status_code=201)
async def create_task(body: TaskCreate, svc: TaskSvc) -> TaskRead:
    return TaskRead.model_validate(await svc.create_task(body))


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(task_id: uuid.UUID, body: TaskUpdate, svc: TaskSvc) -> TaskRead:
    return TaskRead.model_validate(await svc.update_task(task_id, body))


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: uuid.UUID, svc: TaskSvc) -> None:
    await svc.delete_task(task_id)
