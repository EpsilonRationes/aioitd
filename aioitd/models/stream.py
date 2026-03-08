from typing import Annotated
from uuid import UUID

from pydantic import Field

from aioitd.models.base import ITDBaseModel
from aioitd.models.notifications import Notification


class SSEEvent(ITDBaseModel):
    event: str
    data: dict | None


class ConnectedEvent(ITDBaseModel):
    user_id: Annotated[UUID, Field(alias="userId")]
    timestamp: int


class NotificationEvent(Notification):
    user_id: Annotated[UUID, Field(alias="userId")]
    sound: bool


__all__ = [SSEEvent, ConnectedEvent, NotificationEvent]
