import uuid
from collections.abc import Sequence

from clara.notifications.models import Notification
from clara.notifications.repository import NotificationRepository
from clara.notifications.schemas import NotificationMarkRead


class NotificationService:
    def __init__(self, repo: NotificationRepository) -> None:
        self.repo = repo

    async def list_notifications(self, *, limit: int = 100) -> Sequence[Notification]:
        return await self.repo.list_for_user(limit=limit)

    async def unread_count(self) -> int:
        return await self.repo.unread_count()

    async def mark_notification(
        self, notification_id: uuid.UUID, body: NotificationMarkRead
    ) -> Notification:
        return await self.repo.update(notification_id, read=body.read)

    async def mark_all_read(self) -> None:
        await self.repo.mark_all_read()

    async def clear_read(self) -> None:
        await self.repo.clear_read()

    async def delete_notification(self, notification_id: uuid.UUID) -> None:
        await self.repo.soft_delete(notification_id)
