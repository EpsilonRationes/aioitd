import typing
from typing import Optional, Annotated, Literal, Union
from uuid import UUID

from pydantic import ConfigDict, Field

from aioitd.models.base import ITDBaseModel
from aioitd.objects.base import *
from aioitd.objects.files import FileRef

if typing.TYPE_CHECKING:
    from aioitd.client import AsyncITDClient
    from aioitd.models import Post, Comment, TotalPagination, UpdatePostResponse, Poll, Report
    from aioitd.api import CommentSort, Reason


class OptionRef(ITDBaseModel):
    id: UUID

    model_config = ConfigDict(
        **ITDBaseModel.model_config,
        arbitrary_types_allowed=True
    )

    def __init__(self, option_id: UUID | str | None = None, client: Optional['AsyncITDClient'] = None, **data):
        if option_id is not None:
            identifier = validate_uuid(option_id)
            data['id'] = identifier

        super().__init__(**data)

    def _get_id(self) -> UUID:
        return self.id


class PostRef(ITDBaseModel):
    id: UUID
    client: Annotated[Optional['AsyncITDClient'], Field(exclude=True)] = None

    model_config = ConfigDict(
        **ITDBaseModel.model_config,
        arbitrary_types_allowed=True
    )

    def __init__(self, post_id: UUID | str | None = None, client: Optional['AsyncITDClient'] = None, **data):
        if post_id is not None:
            identifier = validate_uuid(post_id)
            data['id'] = identifier
        if client is not None:
            data['client'] = client

        super().__init__(**data)

    def _get_id(self) -> UUID:
        return self.id

    @require_client
    async def get_full(self, **kwargs) -> tuple[list['Comment'], 'Post']:
        """Получить пост с комментариями.

        Returns:
            Кортеж (список комментариев, пост)

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: пост не существует, удалён, владелец поста забанил,
                           пост принадлежит пользователю с is_private=True,
                           на которого вы не подписаны
        """
        return await self.client.get_post(self._get_id(), **kwargs)

    @require_client
    async def delete(self, **kwargs) -> None:
        """Удалить пост.

        Raises:
            UnauthorizedError: ошибка авторизации
            ForbiddenError: Нет прав для удаления поста
            NotFoundError: Пост не найден
        """
        await self.client.delete_post(self._get_id(), **kwargs)

    @require_client
    async def restore(self, **kwargs) -> None:
        """Восстановить пост.

        Raises:
            UnauthorizedError: ошибка авторизации
            ForbiddenError: Нет прав для восстановления поста
            NotFoundError: Пост не найден
        """
        await self.client.restore_post(self._get_id(), **kwargs)

    @require_client
    async def like(self, **kwargs) -> int:
        """Лайкнуть пост.

        Returns:
            Новое количество лайков

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: Пост не найден
        """
        return await self.client.like_post(self._get_id(), **kwargs)

    @require_client
    async def unlike(self, **kwargs) -> int:
        """Убрать лайк с поста.

        Returns:
            Новое количество лайков

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: Пост не найден
        """
        return await self.client.unlike_post(self._get_id(), **kwargs)

    @require_client
    async def view(self, **kwargs) -> None:
        """Зафиксировать просмотр поста.

        Raises:
            UnauthorizedError: ошибка авторизации
        """
        await self.client.view_post(self._get_id(), **kwargs)

    @require_client
    async def pin(self, **kwargs) -> bool:
        """Закрепить пост на своей стене.

        Returns:
            Успешность операции

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: Пост не найден
            ForbiddenError: Можно прикреплять посты только на своей стене
        """
        return await self.client.pin_post(self._get_id(), **kwargs)

    @require_client
    async def unpin(self, **kwargs) -> bool:
        """Открепить пост со своей стены.

        Returns:
            Успешность операции

        Raises:
            UnauthorizedError: ошибка авторизации
            NotPinedError: Пост не прикреплён
        """
        return await self.client.unpin_post(self._get_id(), **kwargs)

    @require_client
    async def get_comments(
            self,
            cursor: str | None = None,
            limit: int = 20,
            sort: CommentSort | Literal["popular", "newest", "oldest"] = "popular",
            **kwargs
    ) -> tuple['TotalPagination', list['Comment']]:
        """Получить комментарии под постом.

        Args:
            cursor: курсор следующей страницы
            limit: максимальное количество комментариев (1 <= limit <= 500)
            sort: сортировка ("popular", "newest", "oldest")

        Returns:
            Кортеж (пагинация с общим количеством, список комментариев)

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: Пост не найден
        """
        return await self.client.get_post_comments(self._get_id(), cursor, limit, sort, **kwargs)

    @require_client
    async def vote(self, option_ids: list[Union[UUID, str, OptionRef]], **kwargs) -> 'Poll':
        """Проголосовать в опросе.

        Args:
            option_ids: список выбранных вариантов (можно передавать как UUID, строки или OptionRef)

        Returns:
            Обновлённый опрос

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: пост не найден
            ValidationError: Один или несколько вариантов не принадлежат этому опросу
            ValidationError: В этом опросе можно выбрать только один вариант
            ValidationError: len(option_ids) > 0
        """
        processed_options = [
            opt._get_id() if isinstance(opt, OptionRef) else opt
            for opt in option_ids
        ]
        return await self.client.vote_poll(self._get_id(), processed_options, **kwargs)

    @require_client
    async def update(self, content: str, spans: list = None, **kwargs) -> 'UpdatePostResponse':
        """Изменить текст поста.

        Args:
            content: Новый текст поста
            spans: Форматирование текста (список объектов форматирования)

        Returns:
            Обновлённый пост (содержит дату редактирования)

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: Пост не найден
            ValidationError: 1 <= len(content) <= 1_000
            ForbiddenError: Нет прав для редактирования этого поста
            EditWindowExpiredError: пост нельзя изменять спустя несколько дней
            ParamsValidationError: span[i].offset >= 0
            ParamsValidationError: span[i].length > 0
            ParamsValidationError: len(span[i].url) <= 2048
        """
        return await self.client.update_post(self._get_id(), content, spans, **kwargs)

    @require_client
    async def repost(self, content: str = "", **kwargs) -> 'Post':
        """Сделать репост этого поста.

        Args:
            content: Текст репоста (необязательно)

        Returns:
            Созданный репост

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: Пост не найден
            ConflictError: Нельзя репостнуть два раза
            ValidationError: Нельзя репостить свои посты
            ValidationError: len(content) <= 1_000
        """
        return await self.client.repost(self._get_id(), content, **kwargs)

    @require_client
    async def comment(
            self,
            content: str = "",
            attachment_ids: Union[list[Union[UUID, str, FileRef]], None] = None,
            **kwargs
    ) -> 'Comment':
        """Создать комментарий к посту.

        Args:
            content: текст комментария
            attachment_ids: список прикреплённых файлов (можно передавать как UUID, строки или FileRef) (максимум 4)

        Returns:
            Созданный комментарий

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: пост не найден
            ITDError: файл с указанным UUID не существует
            ValidationError: нельзя создать пустой комментарий (без текста и вложений)
            ParamsValidationError: len(attachment_ids) <= 4
            ParamsValidationError: len(content) <= 1_000
        """
        if attachment_ids is not None:
            attachment_ids = [
                aid._get_id() if isinstance(aid, FileRef) else aid
                for aid in attachment_ids
            ]
        return await self.client.comment(self._get_id(), content, attachment_ids, **kwargs)

    @require_client
    async def report(
            self,
            reason: Reason | Literal[
                "spam", "violence", "hate", "adult", "misinfo", "other"
            ] = "other",
            description: str = "",
            **kwargs
    ) -> Report:
        """Написать донос на пост.

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
        return await self.client.report(self._get_id(), 'post', reason, description, **kwargs)


__all__ = ['PostRef', 'OptionRef']