import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from clara.deps import CurrentUser, Db, VaultAccess
from clara.notifications.repository import NotificationRepository
from clara.notifications.schemas import (
    NotificationMarkRead,
    NotificationRead,
    UnreadCount,
)
from clara.notifications.service import NotificationService

router = APIRouter()


def get_notification_service(
    vault_id: uuid.UUID, db: Db, _access: VaultAccess, user: CurrentUser
) -> NotificationService:
    repo = NotificationRepository(session=db, vault_id=vault_id, user_id=user.id)
    return NotificationService(repo=repo)


NotifSvc = Annotated[NotificationService, Depends(get_notification_service)]


@router.get("", response_model=list[NotificationRead])
async def list_notifications(svc: NotifSvc) -> list[NotificationRead]:
    items = await svc.list_notifications()
    return [NotificationRead.model_validate(n) for n in items]


@router.get("/unread-count", response_model=UnreadCount)
async def unread_count(svc: NotifSvc) -> UnreadCount:
    count = await svc.unread_count()
    return UnreadCount(count=count)


@router.patch("/{notification_id}", response_model=NotificationRead)
async def mark_notification(
    notification_id: uuid.UUID,
    body: NotificationMarkRead,
    svc: NotifSvc,
) -> NotificationRead:
    n = await svc.mark_notification(notification_id, body)
    return NotificationRead.model_validate(n)


@router.post("/mark-all-read", status_code=204)
async def mark_all_read(svc: NotifSvc) -> None:
    await svc.mark_all_read()


@router.delete("/clear-read", status_code=204)
async def clear_read_notifications(svc: NotifSvc) -> None:
    await svc.clear_read()


@router.delete("/{notification_id}", status_code=204)
async def delete_notification(
    notification_id: uuid.UUID, svc: NotifSvc
) -> None:
    await svc.delete_notification(notification_id)
