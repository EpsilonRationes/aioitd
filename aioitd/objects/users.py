import typing
from typing import Optional, Annotated, Union, Literal
from uuid import UUID

from pydantic import ConfigDict, Field

from aioitd.models.base import ITDBaseModel
from aioitd.objects.base import *

if typing.TYPE_CHECKING:
    from aioitd.client import AsyncITDClient
    from aioitd.models import Pagination, PagePagination, Post, UserWithFollowing, FullUser, UserBlockedByMe, \
        UserBlockMe, PrivateUser, Report
    from aioitd.api import PostSort, Reason


class UserRef(ITDBaseModel):
    id: UUID | None = None
    username: str | None = None
    client: Annotated[Optional[AsyncITDClient], Field(exclude=True)] = None

    model_config = ConfigDict(
        **ITDBaseModel.model_config,
        arbitrary_types_allowed=True
    )

    def __init__(self, username_or_id: UUID | str | None = None, client: Optional[AsyncITDClient] = None, **data):
        if username_or_id is not None:
            identifier = validate_username_or_uuid(username_or_id)
            if isinstance(identifier, str):
                data['username'] = identifier
            else:
                data['id'] = identifier
        if client is not None:
            data['client'] = client

        super().__init__(**data)

    def _get_id(self) -> str | UUID:
        if self.id is not None:
            return self.id
        if self.username is not None:
            return self.username
        raise ValueError(f"{self.__class__.__name__} необходим id или username")

    @require_client
    async def follow(self, **kwargs) -> int:
        """Подписаться на пользователя.

        Returns:
            Количество подписчиков пользователя

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: Пользователь не найден
            ConflictError: Вы уже подписаны на этого пользователя
            ValidationError: Нельзя подписаться на себя
            UserBlockedError: пользователь заблокирован
        """
        return await self.client.follow(self._get_id(), **kwargs)

    @require_client
    async def unfollow(self, **kwargs) -> int:
        """Отписаться от пользователя.

        Returns:
            Количество подписчиков пользователя

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: Пользователь не найден
        """
        return await self.client.unfollow(self._get_id(), **kwargs)

    @require_client
    async def get_followers(
            self,
            page: int = 1,
            limit: int = 30,
            **kwargs
    ) -> tuple[PagePagination, list[UserWithFollowing]]:
        """Получить подписчиков пользователя.

        Args:
            page: страница (page >= 1)
            limit: максимальное количество пользователей на странице (1 <= limit <= 100)

        Returns:
            Кортеж (пагинация, список пользователей)

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: Пользователь не найден
            UserBlockedError: пользователь заблокирован
        """
        return await self.client.get_followers(self._get_id(), page, limit, **kwargs)

    @require_client
    async def get_following(
            self,
            page: int = 1,
            limit: int = 30,
            **kwargs
    ) -> tuple[PagePagination, list[UserWithFollowing]]:
        """Получить подписки пользователя.

        Args:
            page: страница (page >= 1)
            limit: максимальное количество пользователей на странице (1 <= limit <= 100)

        Returns:
            Кортеж (пагинация, список пользователей)

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: Пользователь не найден
            UserBlockedError: пользователь заблокирован
        """
        return await self.client.get_following(self._get_id(), page, limit, **kwargs)

    @require_client
    async def block(self, **kwargs) -> None:
        """Заблокировать пользователя.

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: пользователь не найден
            ConflictError: пользователь уже заблокирован
            ValidationError: нельзя заблокировать себя
        """
        await self.client.block(self._get_id(), **kwargs)

    @require_client
    async def unblock(self, **kwargs) -> None:
        """Разблокировать пользователя.

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: пользователь не найден
            ConflictError: пользователь не заблокирован
        """
        await self.client.unblock(self._get_id(), **kwargs)

    @require_client
    async def get_full(self, **kwargs) -> Union[FullUser, UserBlockedByMe, UserBlockMe, PrivateUser]:
        """Получить полные данные пользователя.

        Returns:
            Данные пользователя в зависимости от статуса (полный профиль, заблокирован, приватный и т.д.)

        Raises:
            UnauthorizedError: необходима авторизация
            NotFoundError: пользователь не найден
            UserBlockedError: пользователь заблокирован
        """
        return await self.client.get_user(self._get_id(), **kwargs)

    @require_client
    async def get_posts(
            self,
            cursor: str | None = None,
            limit: int = 20,
            sort: PostSort | Literal["new", "popular"] = 'new',
            **kwargs
    ) -> tuple[Pagination, list[Post]]:
        """Посты на стене пользователя (включая его собственные).

        Args:
            cursor: курсор следующей страницы (из предыдущего ответа)
            limit: максимальное количество постов (1 <= limit <= 50)
            sort: сортировка ("new" или "popular")

        Returns:
            Кортеж (пагинация, список постов)

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: пользователь не найден
            UserBlockedError: пользователь заблокирован
        """
        return await self.client.get_posts_by_user(self._get_id(), cursor, limit, sort, **kwargs)

    @require_client
    async def get_liked_posts(
            self,
            cursor: str | None = None,
            limit: int = 20,
            sort: PostSort | Literal["new", "popular"] = 'new',
            **kwargs
    ) -> tuple[Pagination, list[Post]]:
        """Посты, которые лайкнул пользователь.

        Args:
            cursor: курсор следующей страницы
            limit: максимальное количество постов (1 <= limit <= 50)
            sort: сортировка ("new" или "popular")

        Returns:
            Кортеж (пагинация, список постов)

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: пользователь не найден
            UserBlockedError: пользователь заблокирован
        """
        return await self.client.get_liked_posts(self._get_id(), cursor, sort, limit, **kwargs)

    @require_client
    async def get_wall_posts(
            self,
            cursor: str | None = None,
            limit: int = 20,
            sort: PostSort | Literal["new", "popular"] = 'new',
            **kwargs
    ) -> tuple[Pagination, list[Post]]:
        """Посты на стене пользователя, сделанные другими пользователями.

        Args:
            cursor: курсор следующей страницы
            limit: максимальное количество постов (1 <= limit <= 50)
            sort: сортировка ("new" или "popular")

        Returns:
            Кортеж (пагинация, список постов)

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: пользователь не найден
            UserBlockedError: пользователь заблокирован
        """
        return await self.client.get_wall_posts(self._get_id(), cursor, limit, sort, **kwargs)

    @require_client
    async def is_following(self, **kwargs) -> bool:
        """Проверить, подписан ли текущий клиент на этого пользователя.

        Требуется, чтобы у пользователя был указан `id` (UUID).

        Returns:
            Подписан ли

        Raises:
            UnauthorizedError: ошибка авторизации
        """
        id = self._get_id()
        if isinstance(id, str):
            raise ValueError("Требуется, чтобы у пользователя был указан `id` (UUID).")
        response = await self.client.get_follow_status([self._get_id()], **kwargs)
        return next(iter(response.values()))

    @require_client
    async def report(
            self,
            reason: Reason | Literal[
                "spam", "violence", "hate", "adult", "misinfo", "other"
            ] = "other",
            description: str = "",
            **kwargs
    ) -> Report:
        """Написать донос на пользователя.

        Требуется, чтобы у пользователя был указан `id` (UUID).

        Args:
            reason: причина
            description: текст репорта

        Returns:
            Донос

        Raises:
            UnauthorizedError: ошибка авторизации
            ValidationError: не найден пост, пользователь или комментарий по target_id
            ValidationError: нельзя отправить жалобу на один и тот же контент
        """
        id = self._get_id()
        if isinstance(id, str):
            raise ValueError("Требуется, чтобы у пользователя был указан `id` (UUID).")
        return await self.client.report(id, 'user', reason, description, **kwargs)


__all__ = ['UserRef']
