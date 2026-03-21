import typing
from typing import Optional, Annotated
from uuid import UUID

from pydantic import ConfigDict, Field

from aioitd.models.base import ITDBaseModel
from aioitd.objects.base import *

if typing.TYPE_CHECKING:
    from aioitd.client import AsyncITDClient
    from aioitd.models import GetFile


class FileRef(ITDBaseModel):
    id: UUID
    client: Annotated[Optional['AsyncITDClient'], Field(exclude=True)] = None

    model_config = ConfigDict(
        **ITDBaseModel.model_config,
        arbitrary_types_allowed=True
    )

    def __init__(self, file_id: UUID | str | None = None, client: Optional['AsyncITDClient'] = None, **data):
        if file_id is not None:
            identifier = validate_uuid(file_id)
            data['id'] = identifier
        if client is not None:
            data['client'] = client

        super().__init__(**data)

    def _get_id(self) -> UUID:
        return self.id

    @require_client
    async def get_info(self, **kwargs) -> 'GetFile':
        """Получить информацию о файле.

        Returns:
            Файл с датой создания

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: файл не найден или нет доступа
        """
        return await self.client.get_file(self._get_id(), **kwargs)

    @require_client
    async def delete(self, **kwargs) -> None:
        """Удалить файл.

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: файл не найден или нет прав доступа к нему
        """
        await self.client.delete_file(self._get_id(), **kwargs)


__all__ = ['FileRef']
