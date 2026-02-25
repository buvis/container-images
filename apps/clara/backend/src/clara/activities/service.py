import uuid
from collections.abc import Sequence

from clara.activities.models import Activity, ActivityType
from clara.activities.repository import (
    ActivityParticipantRepository,
    ActivityRepository,
    ActivityTypeRepository,
)
from clara.activities.schemas import (
    ActivityCreate,
    ActivityTypeCreate,
    ActivityTypeUpdate,
    ActivityUpdate,
    ParticipantInput,
)
from clara.exceptions import NotFoundError


class ActivityTypeService:
    def __init__(self, repo: ActivityTypeRepository) -> None:
        self.repo = repo

    async def list_types(
        self, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[ActivityType], int]:
        return await self.repo.list(offset=offset, limit=limit)

    async def get_type(self, type_id: uuid.UUID) -> ActivityType:
        t = await self.repo.get_by_id(type_id)
        if t is None:
            raise NotFoundError("ActivityType", type_id)
        return t

    async def create_type(self, data: ActivityTypeCreate) -> ActivityType:
        return await self.repo.create(**data.model_dump())

    async def update_type(
        self, type_id: uuid.UUID, data: ActivityTypeUpdate
    ) -> ActivityType:
        return await self.repo.update(
            type_id, **data.model_dump(exclude_unset=True)
        )

    async def delete_type(self, type_id: uuid.UUID) -> None:
        await self.repo.soft_delete(type_id)


class ActivityService:
    def __init__(
        self,
        repo: ActivityRepository,
        participant_repo: ActivityParticipantRepository,
    ) -> None:
        self.repo = repo
        self.participant_repo = participant_repo

    async def list_activities(
        self, *, offset: int = 0, limit: int = 50, q: str | None = None
    ) -> tuple[Sequence[Activity], int]:
        return await self.repo.list(offset=offset, limit=limit, q=q)

    async def list_by_contact(
        self,
        contact_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[Activity], int]:
        return await self.repo.list_by_contact(
            contact_id, offset=offset, limit=limit
        )

    async def get_activity(self, activity_id: uuid.UUID) -> Activity:
        activity = await self.repo.get_by_id(activity_id)
        if activity is None:
            raise NotFoundError("Activity", activity_id)
        return activity

    async def create_activity(self, data: ActivityCreate) -> Activity:
        participants = data.participants
        activity = await self.repo.create(
            **data.model_dump(exclude={"participants"})
        )
        await self._set_participants(activity.id, participants)
        return await self.get_activity(activity.id)

    async def update_activity(
        self, activity_id: uuid.UUID, data: ActivityUpdate
    ) -> Activity:
        payload = data.model_dump(exclude_unset=True, exclude={"participants"})
        if payload:
            await self.repo.update(activity_id, **payload)
        if data.participants is not None:
            await self._replace_participants(activity_id, data.participants)
        return await self.get_activity(activity_id)

    async def delete_activity(self, activity_id: uuid.UUID) -> None:
        await self.repo.soft_delete(activity_id)

    async def add_participant(
        self, activity_id: uuid.UUID, contact_id: uuid.UUID, role: str = ""
    ) -> None:
        await self.participant_repo.create(
            activity_id=activity_id, contact_id=contact_id, role=role
        )

    async def remove_participant(self, participant_id: uuid.UUID) -> None:
        await self.participant_repo.soft_delete(participant_id)

    async def _set_participants(
        self,
        activity_id: uuid.UUID,
        participants: list[ParticipantInput],
    ) -> None:
        for p in participants:
            await self.participant_repo.create(
                activity_id=activity_id,
                contact_id=p.contact_id,
                role=p.role,
            )

    async def _replace_participants(
        self,
        activity_id: uuid.UUID,
        participants: list[ParticipantInput],
    ) -> None:
        await self.participant_repo.delete_by_activity(activity_id)
        await self._set_participants(activity_id, participants)
