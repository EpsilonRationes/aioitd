import typing
from typing import Optional, Annotated, Literal, Union
from uuid import UUID

from pydantic import ConfigDict, Field

from aioitd.models.base import ITDBaseModel
from aioitd.objects.base import *
from aioitd.objects.users import UserRef
from aioitd.objects.files import FileRef


if typing.TYPE_CHECKING:
    from aioitd.client import AsyncITDClient
    from aioitd.models import Report, UpdateCommentResponse, Reply
    from aioitd.api import Reason


class CommentRef(ITDBaseModel):
    id: UUID
    client: Annotated[Optional['AsyncITDClient'], Field(exclude=True)] = None

    model_config = ConfigDict(
        **ITDBaseModel.model_config,
        arbitrary_types_allowed=True
    )

    def __init__(self, comment_id: UUID | str | None = None, client: Optional['AsyncITDClient'] = None, **data):
        if comment_id is not None:
            identifier = validate_uuid(comment_id)
            data['id'] = identifier
        if client is not None:
            data['client'] = client

        super().__init__(**data)

    def _get_id(self) -> UUID:
        return self.id

    @require_client
    async def edit(self, content: str, **kwargs) -> 'UpdateCommentResponse':
        """Редактировать комментарий.

        Args:
            content: новый текст комментария

        Returns:
            Обновлённый комментарий (содержит дату редактирования)

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: комментарий не найден
            ForbiddenError: нет прав на редактирование этого комментария
            ParamsValidationError: 1 <= len(content) <= 1_000
        """
        return await self.client.edit_comment(self._get_id(), content, **kwargs)

    @require_client
    async def delete(self, **kwargs) -> None:
        """Удалить комментарий.

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: комментарий не найден
            ForbiddenError: нет прав на удаление комментария
        """
        await self.client.delete_comment(self._get_id(), **kwargs)

    @require_client
    async def restore(self, **kwargs) -> None:
        """Восстановить удалённый комментарий.

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: комментарий не найден
            ForbiddenError: нет прав на восстановление комментария
        """
        await self.client.restore_comment(self._get_id(), **kwargs)

    @require_client
    async def like(self, **kwargs) -> int:
        """Поставить лайк на комментарий.

        Returns:
            Обновлённое количество лайков

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: комментарий не найден
        """
        return await self.client.like_comment(self._get_id(), **kwargs)

    @require_client
    async def unlike(self, **kwargs) -> int:
        """Убрать лайк с комментария.

        Returns:
            Обновлённое количество лайков

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: комментарий не найден
        """
        return await self.client.unlike_comment(self._get_id(), **kwargs)

    @require_client
    async def reply(
            self,
            content: str = "",
            replay_to_user_id: Union[UUID, str, UserRef, None] = None,
            attachment_ids: Union[list[Union[UUID, str, FileRef]], None] = None,
            **kwargs
    ) -> 'Reply':
        """Ответить на этот комментарий.

        Args:
            content: текст ответа
            replay_to_user_id: пользователь, которому адресован ответ (можно передать UserRef)
            attachment_ids: список прикреплённых файлов (можно передать FileRef)

        Returns:
            Созданный ответ

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: комментарий не найден
            ValidationError: нельзя создать пустой ответ (без текста и вложений)
            ITDError: файл с указанным UUID не существует
            ParamsValidationError: len(attachment_ids) <= 4
            ParamsValidationError: len(content) <= 1_000
        """
        if replay_to_user_id is not None:
            if isinstance(replay_to_user_id, UserRef):
                replay_to_user_id = replay_to_user_id._get_id()

        if attachment_ids is not None:
            attachment_ids = [
                aid._get_id() if isinstance(aid, FileRef) else aid
                for aid in attachment_ids
            ]
        return await self.client.replies(
            self._get_id(),
            content,
            replay_to_user_id,
            attachment_ids,
            **kwargs
        )

    @require_client
    async def report(
            self,
            reason: Reason | Literal[
                "spam", "violence", "hate", "adult", "misinfo", "other"
            ] = "other",
            description: str = "",
            **kwargs
    ) -> 'Report':
        """Написать донос на комментарий.

        Args:
            reason: причина
            description: текст репорта

        Returns:
            Донос

        Raises:
            UnauthorizedError: ошибка авторизации
            ValidationError: не найден пост, пользователь или комментарий по target_id
            ValidationError: нельзя отправить жалобу на один и тот же контент
            ParamsValidationError: len(description) <= 1000
        """
        return await self.client.report(self._get_id(), 'comment', reason, description, **kwargs)


__all__ = ['CommentRef']