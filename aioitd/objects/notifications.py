import typing
from typing import Optional, Annotated
from uuid import UUID

from pydantic import ConfigDict, Field

from aioitd.models.base import ITDBaseModel
from aioitd.objects.base import validate_uuid, require_client

if typing.TYPE_CHECKING:
    from aioitd.client import AsyncITDClient


class NotificationRef(ITDBaseModel):
    id: UUID
    client: Annotated[Optional['AsyncITDClient'], Field(exclude=True)] = None

    model_config = ConfigDict(
        **ITDBaseModel.model_config,
        arbitrary_types_allowed=True
    )

    def __init__(self, notification_id: UUID | str | None = None, client: Optional['AsyncITDClient'] = None, **data):
        if notification_id is not None:
            identifier = validate_uuid(notification_id)
            data['id'] = identifier
        if client is not None:
            data['client'] = client
        super().__init__(**data)

    def _get_id(self) -> UUID:
        return self.id

    @require_client
    async def read(self, **kwargs) -> bool:
        """Пометить уведомление прочитанным.

        Returns:
            Успешна ли операция

        Raises:
            UnauthorizedError: ошибка авторизации
        """
        return await self.client.read_notification(self._get_id(), **kwargs)


__all__ = ['NotificationRef']