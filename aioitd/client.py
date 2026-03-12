from contextlib import asynccontextmanager
from datetime import datetime
from functools import wraps
from typing import IO, Any, TypeVar, ParamSpec, Callable, Awaitable, Literal, AsyncIterator, \
    AsyncGenerator
import asyncio
from uuid import UUID

from httpx import AsyncClient

from aioitd.api.posts import ComemntSort
from aioitd.models import *
from aioitd.api import *
from aioitd.fetch import is_token_expired, decode_jwt_payload

P = ParamSpec("P")
T = TypeVar("T")


class AsyncITDClient:
    def __init__(
            self,
            refresh_token: str = "",
            timeout: int = 10,
            file_upload_timeout: int = 60,
            client: AsyncClient = None,
            domain: str = "xn--d1ah4a.com"
    ):
        """Асинхронный клиент итд.com. Обновляет access токен.

        Args:
            refresh_token: refresh токен, если не указан, можно отправить запрос только на ендпоинты, не требующие авторизации
            timeout: таймаут запросов
            file_upload_timeout: таймаут на загрузку файла
            client: Если нужно создать несколько `AsyncITDClient` с одним клиентом `httpx.AsyncClient`. Если указан: `AsyncITDClient.close()` не будет закрывать `httpx.AsyncClient`
            domain: Домен запросов

        Examples:
            ```python
            refresh_token = "ВАШ ТОКЕН"
            async with AsyncITDClient(refresh_token) as client:
                await client.get_posts()
                has_more, notifications = await client.get_notifications()
            ```

            Без токена:

            ```python
            async with AsyncITDClient() as client:
                hashtags = await client.search_hashtags('1')
            ```

            Без `with`:

            ```python
            client = AsyncITDClient("ВАШ ТОКЕН")
            ...
            await client.close()
            ```
        """
        self.timeout = timeout
        self.file_upload_timeout = file_upload_timeout
        if client is not None:
            self.client = client
            self.__close_client = False
        else:
            self.client = AsyncClient()
            self.__close_client = True
        self.refresh_token = refresh_token
        self._access_token = None
        self.__refresh_lock = asyncio.Lock()
        self.domain = domain

    async def __aenter__(self) -> AsyncITDClient:
        return self

    async def close(self) -> None:
        """Закрывает httpx сессию.

        Examples:
            ```python
            client = AsyncITDClient(...)
            ...
            await client.close()
            ```

        """
        await self.client.aclose()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.__close_client:
            await self.close()

    async def refresh(self, **kwargs) -> None:
        """Обновить `access_token`

        Raises:
            TokenNotFoundError: Такого токена не существует
            TokenRevokedError: Токен отозван
            TokenMissingError: Токен не указан (равен пустой строке)
            TokenExpiredError: Токен истёк
        """
        self._access_token = await refresh(self.client, self.refresh_token, self.domain, timeout=self.timeout, **kwargs)

    async def _refresh_with_lock(self):
        async with self.__refresh_lock:
            if self.is_token_expired():
                await self.refresh()

    def is_token_expired(self) -> bool:
        """Просрочен ли access токен"""
        return self._access_token is None or is_token_expired(self._access_token)

    @staticmethod
    def auth_required(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @wraps(func)
        async def wrapper(self: AsyncITDClient, *args, **kwargs) -> Any:
            if self.is_token_expired():
                await self._refresh_with_lock()
            return await func(self, *args, **kwargs)

        return wrapper

    async def logout(self, **kwargs) -> None:
        """Выйти из аккаунта, отозвать refresh токен. Работает при любом токене: просроченном, не существующим, пустой строкой."""
        await logout(self.client, self.domain, self.refresh_token, timeout=self.timeout, **kwargs)
        self._access_token = None

    @auth_required
    async def change_password(
            self,
            old_password: str,
            new_password: str,
            **kwargs
    ) -> None:
        """Поменять пароль. При успешной смене пароля `refresh_token` отзывается.

        Args:
            old_password: старый пароль
            new_password: новый пароль

        Raises:
            UnauthorizedError: ошибка авторизации
            InvalidPasswordError: Пароль не подходит под условия
            InvalidOldPasswordError: Указан неверный старый пароль
            SomePasswordError: Новый пароль должен отличать от старого

        """
        await change_password(
            self.client, self._access_token, old_password, new_password, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def get_me_uuid(self) -> UUID:
        """Получить uuid из access токена"""
        return UUID(decode_jwt_payload(self._access_token)['sub'])

    async def search_hashtags(self, query: str, limit: int = 20, **kwargs) -> list[Hashtag]:
        """Поиск хештегов.

        Args:
            query: текст запроса
            limit: максимальное количество выданных хештегов

        Returns:
            Список найденных хештегов

        Raises:
            ParamsValidationError: 1 <= limit <= 100
            ParamsValidationError: len(query) <= 100
        """
        return await search_hashtags(self.client, query, limit, self.domain, timeout=self.timeout, **kwargs)

    async def get_trending_hashtags(self, limit: int = 10, **kwargs) -> list[Hashtag]:
        """Получить самые популярные хештеги.

        Args:
            limit: максимальное количество выданных хештегов

        Returns:
            Список самых популярных хештегов

        Raises:
            ParamsValidationError: 1 <= limit <= 50
        """
        return await get_trending_hashtags(self.client, limit, self.domain, timeout=self.timeout, **kwargs)

    async def get_posts_by_hashtag(
            self,
            hashtag_name: str,
            cursor: str | None = None,
            limit: int = 20,
            **kwargs
    ) -> tuple[Hashtag, Pagination, list[tuple[list[Comment], Post]]]:
        """Посты по хештегу.

        Args:
            hashtag_name: текст хештега
            cursor: next_cursor предыдущей страницы
            limit: максимальное количество выданных постов

        Returns:
            хештег, пагинация, список из постов и их комментариев

        Raises:
            NotFoundError: Хештег не найден
            ParamsValidationError: 1 <= limit <= 50
        """
        return await get_posts_by_hashtag(
            self.client, hashtag_name, cursor, limit, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def get_notifications(self, offset: int = 0, limit: int = 30, **kwargs) -> tuple[bool, list[Notification]]:
        """Получить уведомления.

        Args:
            offset: сдвиг
            limit: максимально количество уведомлений в ответе, любое число

        Returns:
            bool есть ли ещё уведомления, list[Notification] список уведомлений

        Raises:
            UnauthorizedError: ошибка авторизации
            ITDError: offset >= 0
        """
        return await get_notifications(
            self.client, self._access_token, offset, limit, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def read_batch_notifications(self, notifications_ids: list[UUID], **kwargs) -> int:
        """Пометить прочитанными несколько уведомлений.

        Args:
            notifications_ids: список UUID уведомлений

        Raises:
            UnauthorizedError: ошибка авторизации
            ParamsValidationError: len(notifications_ids) <= 20

        Returns: 
            Количество прочитанных уведомлений
        """
        return await self.read_batch_notifications(
            self.client, self._access_token, notifications_ids, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def read_notification(self, notification_id: UUID, **kwargs) -> bool:
        """Пометить сообщение прочитанным.
        
        Args:
            notification_id: UUID уведомления

        Returns:
            Успешна ли операция
            
        Raises:
            UnauthorizedError: ошибка авторизации

        """
        return await read_notification(self.client, self._access_token, notification_id, self.domain,
                                       timeout=self.timeout, **kwargs)

    @auth_required
    async def get_notifications_count(self, **kwargs) -> int:
        """Получить количество непрочитанных уведомлений.
        
        Raises:
            UnauthorizedError: ошибка авторизации

        Returns: 
            Количество непрочитанных уведомлений.
        """
        return await get_notifications_count(self.client, self._access_token, self.domain, timeout=self.timeout,
                                             **kwargs)

    @auth_required
    async def read_all_notifications(self, **kwargs) -> bool:
        """Пометить все уведомления прочитанными.

        Raises:
            UnauthorizedError: ошибка авторизации

        Returns: 
            Успешна ли операция
        """
        return await read_all_notifications(self.client, self._access_token, self.domain, timeout=self.timeout,
                                            **kwargs)

    @auth_required
    async def get_notification_settings(self, **kwargs) -> NotificationsSettings:
        """Получить настройки уведомлений.

        Raises:
            UnauthorizedError: ошибка авторизации

        Returns:
            Настройки уведомлений
        """
        return await get_notification_settings(self.client, self._access_token, self.domain, timeout=self.timeout,
                                               **kwargs)

    @auth_required
    async def update_notification_settings(
            self,
            comments: bool | None = None,
            enabled: bool | None = None,
            follows: bool | None = None,
            mentions: bool | None = None,
            sound: bool | None = None,
            likes: bool | None = None,
            wall_posts: bool | None = None,
            **kwargs
    ) -> NotificationsSettings:
        """Настроить уведомления

        Args:
            comments: комментарии
            enabled: включены ли уведомления
            follows: подписки
            mentions: упоминания
            sound: звуки при уведомлениях
            likes: лайки
            wall_posts: посты на стене

        Returns:
            Новые настройки уведомлений

        Raises:
            UnauthorizedError: ошибка авторизации
        """
        return await update_notification_settings(self.client, self._access_token, comments, enabled, follows, mentions,
                                                  sound, likes, wall_posts, self.domain, timeout=self.timeout, **kwargs)

    @auth_required
    async def get_file(self, file_id: UUID, **kwargs) -> GetFile:
        """Получить файл.
        
        Args:
            file_id: UUID файла
        
        Returns:
            Файл с датой создания

        Raises:
            UnauthorizedError: ошибка авторизации

        """
        return await get_file(self.client, self._access_token, file_id, self.domain, timeout=self.timeout, **kwargs)

    @auth_required
    async def upload_file(self, file: IO[bytes], **kwargs) -> File:
        """Загрузить файл.

        Args:
            file: файл

        Returns:
            Файл

        Raises:
            UnauthorizedError: ошибка авторизации
            ValidationError: недопустимый тип файла
            TooLargeError: размер запроса слишком большой
            UploadError: ошибка загрузки файла
            ContentModerationError: Не удалось проверить файл

        """
        return await upload_file(
            self.client, self._access_token, file, self.domain, timeout=self.file_upload_timeout, **kwargs
        )

    @auth_required
    async def delete_file(self, file_id: UUID, **kwargs) -> None:
        """Удалить файл.

        Args:
            file_id: UUID файла

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: Файл не найден, или нет прав доступа к нему
        """
        return await delete_file(self.client, self._access_token, file_id, self.domain, timeout=self.timeout, **kwargs)

    @auth_required
    async def report(
            self,
            target_id: UUID,
            target_type: ReportTargetType | Literal[
                "spam", "violence", "hate", "adult", "misinfo", "other"
            ] = ReportTargetType.USER,
            reason: Reason | Literal["post", "comment", "user"] = Reason.OTHER,
            description: str = "",
            **kwargs
    ) -> Report:
        """Пожаловаться
        
        Args:
            target_id: UUID цели
            target_type: тип цели
            reason: причина
            description: текст репорта

        Returns:
            Донос

        Raises:
            UnauthorizedError: ошибка авторизации
            ValidationError: не найден пост, пользователь или комментарий по target_id
            ValidationError: нельзя отправить жалобу на один и тот же контент
            PramsValidationError: len(description) <= 1000
        """
        return await report(
            self.client, self._access_token, target_id, target_type, reason, description, self.domain,
            timeout=self.timeout, **kwargs
        )

    async def search(
            self,
            query: str,
            user_limit: int | None = 20,
            hashtag_limit: int | None = 20,
            **kwargs
    ) -> tuple[list[Hashtag], list[UserWithFollowersCount]]:
        """Поиск

        Args:
            query: запрос
            user_limit: максимальное количество выданных пользователей
            hashtag_limit: максимальное количество выданных хештегов

        Returns:
            найденные хештеги, найденные пользователи

        Raises:
            ParamsValidationError: 1 <= user_limit <= 20
            ParamsValidationError: 1 <= hashtag_limit <= 20
        """
        return await search(
            self.client, query, user_limit, hashtag_limit, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def get_verification_status(self, **kwargs) -> str:
        """Получить статус верификации
        
        Returns:
            Статус верификации
            
        Raises:
            UnauthorizedError: ошибка авторизации

        """
        return await get_verification_status(**kwargs)

    @auth_required
    async def submit_verification(self, video_url: str, **kwargs) -> dict:
        """Подать запрос на галочку
        
        Args:
            video_url: url видео, загруженного на itd

        Raises:
            UnauthorizedError: ошибка авторизации

        """
        return await submit_verification(self.client, video_url, self.domain, timeout=self.timeout, **kwargs)

    @auth_required
    async def get_user(
            self,
            username_or_id: str | UUID,
            **kwargs
    ) -> FullUser | UserBlockedByMe | UserBlockMe | PrivateUser:
        """Получить данные пользователя.

        Args:
            username_or_id: имя пользователя или его UUID

        Raises:
            UnauthorizedError: необходима авторизация
            NotFoundError: пользователь не найден
            UserBlockedError: пользователь заблокирован
        """
        return await get_user(
            self.client, self._access_token, username_or_id, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def get_me(self, **kwargs) -> FullMe | DeletedMe:
        """Получить текущего пользователя.

        Returns:
            FullMe: данные пользователя
            DeletedMe: при удалённом аккаунте

        Raises:
            UnauthorizedError: ошибка авторизации
        """
        return await get_me(
            self.client, self._access_token, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def follow(
            self,
            username_or_id: str | UUID,
            **kwargs
    ) -> int:
        """Подписаться на пользователя

        Args:
            username_or_id: имя пользователя или его UUID

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: Пользователь не найден
            ConflictError: Вы уже подписаны на этого пользователя
            ValidationError: Нельзя подписаться на себя
            UserBlockedError: пользователь заблокирован

        Returns: 
            Количество подписчиков пользователя
        """
        return await follow(
            self.client, self._access_token, username_or_id, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def unfollow(
            self,
            username_or_id: str | UUID,
            **kwargs
    ) -> int:
        """Отписаться от пользователя

        Args:
            username_or_id: имя пользователя или его UUID

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: Пользователь не найден

        Returns: 
            Количество подписчиков пользователя
        """
        return await unfollow(
            self.client, self._access_token, username_or_id, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def get_followers(
            self,
            username_or_id: str | UUID,
            page: int = 1,
            limit: int = 30,
            **kwargs
    ) -> tuple[PagePagination, list[UserWithFollowing]]:
        """Получить подписчиков пользователя.

        Args:
            username_or_id: имя пользователя или его UUID
            page: страница
            limit: максимальное количество пользователей на странице

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: Пользователь не найден
            ParamsValidationError: 1 <= limit <= 100
            ParamsValidationError: page >= 1
            UserBlockedError: пользователь заблокирован
        """
        return await get_followers(
            self.client, self._access_token, username_or_id, page, limit, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def get_following(
            self,
            username_or_id: str | UUID,
            page: int = 1,
            limit: int = 30,
            **kwargs
    ) -> tuple[PagePagination, list[UserWithFollowing]]:
        """Получить подписки пользователя.

        Args:
            username_or_id: имя пользователя или его UUID
            page: страница
            limit: максимальное количество пользователей на странице

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: Пользователь не найден
            ParamsValidationError: 1 <= limit <= 100
            ParamsValidationError: page >= 1
            UserBlockedError: пользователь заблокирован
        """
        return await get_following(
            self.client, self._access_token, username_or_id, page, limit, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def get_top_clans(self, **kwargs) -> list[Clan]:
        """Получить топ кланов.

        Raises:
            UnauthorizedError: ошибка авторизации
        """
        return await get_top_clans(
            self.client, self._access_token, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def get_who_to_follow(self, **kwargs) -> list[UserWithFollowersCount]:
        """Получить топ по подпискам (кого можно подписаться).

        Raises:
            UnauthorizedError: ошибка авторизации
        """
        return await get_who_to_follow(
            self.client, self._access_token, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def search_users(
            self,
            query: str,
            limit: int = 20,
            **kwargs
    ) -> list[UserWithFollowersCount]:
        """Поиск пользователей.

        Args:
            query: текст запроса
            limit: максимальное количество выданных пользователей

        Raises:
            UnauthorizedError: ошибка авторизации
            ValidationError: 1 <= limit <= 50
        """
        return await search_users(
            self.client, self._access_token, query, limit, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def get_pins(self, **kwargs) -> tuple[str | None, list[PinWithDate]]:
        """Получить список пинов и текущий пин.

        Returns:
            (активный пин, список доступных пинов)

        Raises:
            UnauthorizedError: неверный access токен
        """
        return await get_pins(
            self.client, self._access_token, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def set_pin(
            self,
            pin_slug: PinSlug,
            **kwargs
    ) -> PinSlug:
        """Изменить пин.

        Args:
            pin_slug: slug пина

        Raises:
            UnauthorizedError: неверный access токен
            PinNotOwnedError: вы не обладаете этим пином или такого пина не существует
            ParamsValidationError: 1 <= len(slug) <= 50
        """
        return await set_pin(
            self.client, self._access_token, pin_slug, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def delete_pin(self, **kwargs) -> None:
        """Убрать пин.

        Raises:
            UnauthorizedError: неверный access токен
        """
        await delete_pin(
            self.client, self._access_token, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def get_privacy(self, **kwargs) -> Privacy:
        """Получить настройки приватности текущего пользователя.

        Raises:
            UnauthorizedError: неверный access токен
        """
        return await get_privacy(
            self.client, self._access_token, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def update_privacy(
            self,
            is_private: bool | None = None,
            likes_visibility: Visibility | None = None,
            wall_access: Visibility | None = None,
            show_last_seen: bool | None = None,
            **kwargs
    ) -> Privacy:
        """Изменить настройки приватности текущего пользователя.

        Args:
            is_private: приватный ли пользователь
            likes_visibility: кто может видеть лайкнутые посты
            wall_access: кто может писать на стене
            show_last_seen: показывать время последнего посещения

        Raises:
            UnauthorizedError: неверный access токен
        """
        return await update_privacy(
            self.client, self._access_token, is_private, likes_visibility, wall_access, show_last_seen,
            self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def get_profile(self, **kwargs) -> Profile:
        """Профиль текущего пользователя.

        Raises:
            UnauthorizedError: неверный access токен
        """
        return await get_profile(
            self.client, self._access_token, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def update_profile(
            self,
            bio: str | None = None,
            display_name: str | None = None,
            username: str | None = None,
            banner_id: UUID | None = None,
            **kwargs
    ) -> Me:
        """Обновить профиль.

        Args:
            bio: о себе
            display_name: имя
            username: имя пользователя
            banner_id: UUID файла нового баннера

        Raises:
            UnauthorizedError: неверный access токен
            ITDError: Био максимум 160 символов
            ITDError: Имя от 1 до 50 символов
            ITDError: Юзернейм 3-50 символов, только буквы, цифры и _
            ForbiddenError: На баннер можно поставить только свой файл
            ValidationError: Баннер может быть только изображением
            UsernameTakenError: Имя пользователя уже занято
        """
        return await update_profile(
            self.client, self._access_token, bio, display_name, username, banner_id,
            self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def delete_banner(self, **kwargs) -> Me:
        """Удалить баннер.

        Raises:
            UnauthorizedError: неверный access токен
        """
        return await delete_banner(self.client, self._access_token, self.domain, timeout=self.timeout, **kwargs)

    @auth_required
    async def block(
            self,
            username_or_id: str | UUID,
            **kwargs
    ) -> None:
        """Заблокировать пользователя.

        Args:
            username_or_id: имя пользователя или UUID

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: пользователь не найден
            ConflictError: пользователь уже заблокирован
            ValidationError: нельзя заблокировать себя
        """
        await block(
            self.client, self._access_token, username_or_id, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def unblock(
            self,
            username_or_id: str | UUID,
            **kwargs
    ) -> None:
        """Разблокировать пользователя.

        Args:
            username_or_id: имя пользователя или UUID

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: пользователь не найден
            ConflictError: пользователь не заблокирован
        """
        await unblock(
            self.client, self._access_token, username_or_id, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def get_blocked(
            self,
            page: int = 1,
            limit: int = 20,
            **kwargs
    ) -> tuple[PagePagination, list[BlockedAuthor]]:
        """Получить заблокированных пользователей.

        Args:
            page: страница
            limit: максимальное количество пользователей на странице

        Raises:
            UnauthorizedError: неверный access токен
            ParamsValidationError: 1 <= limit <= 100
            ParamsValidationError: page >= 1
        """
        return await get_blocked(
            self.client, self._access_token, page, limit, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def get_follow_status(
            self,
            user_ids: list[UUID],
            **kwargs
    ) -> dict[UUID, bool]:
        """Подписаны ли вы на пользователей.

        Args:
            user_ids: список UUID пользователей

        Raises:
            UnauthorizedError: неверный access токен
            ParamsValidationError: len(user_ids) <= 20
        """
        return await get_follow_status(
            self.client, self._access_token, user_ids, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def delete_account(self, **kwargs) -> datetime:
        """Удалить аккаунт. После удаления аккаунта все остальные эндпоинт, требущие авторизации будут выбрасывать
        AccountDeletedError, кроме get_me и get_me_uuid

        Raises:
            UnauthorizedError: неверный access токен

        Returns:
            Время, до которого можно восстановить аккаунт

        """
        return await delete_account(self.client, self._access_token, self.domain, timeout=self.timeout, **kwargs)

    async def restore_account(self, **kwargs) -> bool:
        """Восстановать аккаунт

        Raises:
            UnauthorizedError: неверный access токен
            NotDeletedError: аккаунт не удалён

        Returns:
            Успешна ли операция

        """
        return await restore_account(self.client, self._access_token, self.domain, timeout=self.timeout, **kwargs)

    @auth_required
    async def get_post(
            self,
            post_id: UUID,
            **kwargs
    ) -> tuple[list[Comment], Post]:
        """Получить пост.

        Args:
            post_id: UUID поста

        Returns:
            Кортеж (список комментариев, пост)

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError:
                пост не существует, удалён, владелец поста забанил, пост принадлежит пользователю с is_private=True,
                на которого вы не подписаны
        """
        return await get_post(
            self.client, self._access_token, post_id, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def delete_post(
            self,
            post_id: UUID,
            **kwargs
    ) -> None:
        """Удалить пост.

        Args:
            post_id: UUID поста

        Raises:
            UnauthorizedError: ошибка авторизации
            ForbiddenError: Нет прав для удаления поста
            NotFoundError: Пост не найден
        """
        await delete_post(
            self.client, self._access_token, post_id, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def restore_post(
            self,
            post_id: UUID,
            **kwargs
    ) -> None:
        """Восстановить пост.

        Args:
            post_id: UUID поста

        Raises:
            UnauthorizedError: ошибка авторизации
            ForbiddenError: Нет прав для восстановления поста
            NotFoundError: Пост не найден
        """
        await restore_post(
            self.client, self._access_token, post_id, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def like_post(
            self,
            post_id: UUID,
            **kwargs
    ) -> int:
        """Лайкнуть пост.

        Args:
            post_id: UUID поста

        Returns:
            Новое количество лайков

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: Пост не найден
        """
        return await like_post(
            self.client, self._access_token, post_id, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def unlike_post(
            self,
            post_id: UUID,
            **kwargs
    ) -> int:
        """Убрать лайк с поста.

        Args:
            post_id: UUID поста

        Returns:
            Новое количество лайков

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: Пост не найден
        """
        return await unlike_post(
            self.client, self._access_token, post_id, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def view_post(
            self,
            post_id: UUID,
            **kwargs
    ) -> None:
        """Зафиксировать просмотр поста.

        Args:
            post_id: UUID поста

        Raises:
            UnauthorizedError: ошибка авторизации
        """
        await view_post(
            self.client, self._access_token, post_id, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def pin_post(
            self,
            post_id: UUID,
            **kwargs
    ) -> bool:
        """Закрепить пост на своей стене.

        Args:
            post_id: UUID поста

        Returns:
            Успешность операции

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: Пост не найден
            ForbiddenError: Можно прикреплять посты только на своей стене
        """
        return await pin_post(
            self.client, self._access_token, post_id, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def unpin_post(
            self,
            post_id: UUID,
            **kwargs
    ) -> bool:
        """Открепить пост со своей стены.

        Args:
            post_id: UUID поста

        Returns:
            Успешность операции

        Raises:
            UnauthorizedError: ошибка авторизации
            NotPinedError: Пост не прикреплён
        """
        return await unpin_post(
            self.client, self._access_token, post_id, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def get_posts_by_user(
            self,
            username_or_id: str | UUID,
            cursor: str | None = None,
            limit: int = 20,
            sort: PostSort | Literal["new", "popular"] = PostSort.NEW,
            **kwargs
    ) -> tuple[Pagination, list[Post]]:
        """Посты на стене пользователя (включая его собственные).

        Args:
            username_or_id: имя пользователя или его UUID
            cursor: курсор следующей страницы (из предыдущего ответа)
            limit: максимальное количество постов
            sort: сортировка ("new" или "popular")

        Returns:
            Кортеж (пагинация, список постов)

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: пользователь не найден
            ValidationError: 1 <= limit <= 50
            UserBlockedError: пользователь заблокирован
        """
        return await get_posts_by_user(
            self.client, self._access_token, username_or_id, cursor, limit, sort,
            self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def get_liked_posts(
            self,
            username_or_id: str | UUID,
            cursor: str | None = None,
            sort: PostSort | Literal["new", "popular"] = PostSort.NEW,
            limit: int = 20,
            **kwargs
    ) -> tuple[Pagination, list[Post]]:
        """Посты, которые лайкнул пользователь.

        Args:
            username_or_id: имя пользователя или его UUID
            cursor: курсор следующей страницы
            limit: максимальное количество постов
            sort: сортировка ("new" или "popular")

        Returns:
            Кортеж (пагинация, список постов)

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: пользователь не найден
            ValidationError: 1 <= limit <= 50
            UserBlockedError: пользователь заблокирован
        """
        return await get_posts_by_user_liked(
            self.client, self._access_token, username_or_id, cursor, limit,
            sort, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def get_wall_posts(
            self,
            username_or_id: str | UUID,
            cursor: str | None = None,
            limit: int = 20,
            sort: PostSort | Literal["new", "popular"] = PostSort.NEW,
            **kwargs
    ) -> tuple[Pagination, list[Post]]:
        """Посты на стене пользователя, сделанные другими пользователями.

        Args:
            username_or_id: имя пользователя или его UUID
            cursor: курсор следующей страницы
            limit: максимальное количество постов
            sort: сортировка ("new" или "popular")

        Returns:
            Кортеж (пагинация, список постов)

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: пользователь не найден
            ValidationError: 1 <= limit <= 50
            UserBlockedError: пользователь заблокирован
        """
        return await get_posts_by_user_wall(
            self.client, self._access_token, username_or_id, cursor, limit,
            sort, self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def get_posts(
            self,
            cursor: str | None = None,
            limit: int = 20,
            tab: Tab | Literal['popular', 'following', 'clan'] = Tab.POPULAR,
            **kwargs
    ) -> tuple[Pagination, list[Post]]:
        """Лента постов.

        Args:
            cursor: курсор следующей страницы
            limit: максимальное количество постов
            tab: вкладка ("popular", "following", "clan")

        Returns:
            Кортеж (пагинация, список постов)

        Raises:
            UnauthorizedError: ошибка авторизации
            ValidationError: 1 <= limit <= 50
        """
        return await get_posts(
            self.client, self._access_token, cursor, limit, tab,
            self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def get_post_comments(
            self,
            post_id: UUID,
            cursor: str | None = None,
            limit: int = 20,
            sort: ComemntSort | Literal["popular", "newest", "oldest"] = ComemntSort.POPULAR,
            **kwargs
    ) -> tuple[TotalPagination, list[Comment]]:
        """Получить комментарии под постом.

        Args:
            post_id: UUID поста
            cursor: курсор следующей страницы
            sort: сортировка ("popular", "newest", "oldest")
            limit: максимальное количество комментариев

        Returns:
            Кортеж (пагинация с общим количеством, список комментариев)

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: Пост не найден
            ParamsValidationError: 1 <= limit <= 500
        """
        return await get_post_comments(
            self.client, self._access_token, post_id, cursor, limit, sort,
            self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def vote_poll(
            self,
            post_id: UUID,
            option_ids: list[UUID],
            **kwargs
    ) -> Poll:
        """Проголосовать в опросе.

        Args:
            post_id: UUID поста
            option_ids: список UUID выбранных вариантов

        Returns:
            Обновлённый опрос

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: пост не найден
            ValidationError: Один или несколько вариантов не принадлежат этому опросу
            ValidationError: В этом опросе можно выбрать только один вариант
            ValidationError: len(option_ids) > 0
        """
        return await vote(
            self.client, self._access_token, post_id, option_ids,
            self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def create_post(
            self,
            content: str = '',
            attachment_ids: list[UUID] | None = None,
            wall_recipient_id: UUID | None = None,
            multiple_choice: bool = False,
            question: str | None = None,
            options: list[str] | None = None,
            spans: list[Monospace | Strike | Underline | Bold | Italic | Spoiler | Link] | None = None,
            **kwargs
    ) -> Post:
        """Создать пост.

        Args:
            content: Текст поста
            attachment_ids: Прикреплённые файлы
            wall_recipient_id: ID пользователя, на чью стену публикуется пост (если не указан, пост идёт на свою стену)
            multiple_choice: Возможен ли множественный выбор в опросе
            question: Заголовок опроса
            options: Варианты ответов (список строк)
            spans: Форматирование текста (список объектов форматирования)

        Returns:
            Созданный пост

        Raises:
            UnauthorizedError: ошибка авторизации
            ValidationError: Нельзя создать пост content="", attachment_ids=[], question=None
            ParamsValidationError: len(content) <= 1_000
            VideoRequiresVerificationError: Загрузка видео доступна только верифицированным пользователям
            ValidationError: len(attachments_ids) <= 10
            ForbiddenError: Некоторые файлы из attachment_ids не существуют
            ParamsValidationError: len(spans) <= 100
            ValidationError: 1 <= len(question) <= 128
            ValidationError: 2 <= len(options) <= 10
            ValidationError: 1 <= len(options[i]) <= 32
        """
        return await create_post(
            self.client, self._access_token, content, attachment_ids, wall_recipient_id,
            multiple_choice, question, options, spans,
            self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def update_post(
            self,
            post_id: UUID,
            content: str,
            **kwargs
    ) -> UpdatePostResponse:
        """Изменить текст поста.

        Args:
            post_id: UUID поста
            content: Новый текст поста

        Returns:
            Обновлённый пост (содержит дату редактирования)

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: Пост не найден
            ValidationError: 1 <= len(content) <= 1_000
            ForbiddenError: Нет прав для редактирования этого поста
            EditWindowExpiredError: пост нельзя изменять спустя несколько дней
        """
        return await update_post(
            self.client, self._access_token, post_id, content,
            self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def repost(
            self,
            post_id: UUID,
            content: str = "",
            **kwargs
    ) -> Post:
        """Сделать репост.

        Args:
            post_id: UUID оригинального поста
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
        return await repost(
            self.client, self._access_token, post_id, content,
            self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def comment(
            self,
            post_id: UUID,
            content: str = "",
            attachment_ids: list[UUID] | None = None,
            **kwargs
    ) -> Comment:
        """Создать комментарий к посту.

        Args:
            post_id: UUID поста
            content: текст комментария
            attachment_ids: список UUID прикреплённых файлов (максимум 4)

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
        return await comment(
            self.client, self._access_token, post_id, content, attachment_ids,
            self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def replies(
            self,
            comment_id: UUID,
            content: str = "",
            replay_to_user_id: UUID | None = None,
            attachment_ids: list[UUID] | None = None,
            **kwargs
    ) -> Reply:
        """Ответить на комментарий.

        Args:
            comment_id: UUID комментария, на который отвечаем
            content: текст ответа
            replay_to_user_id: UUID пользователя, которому адресован ответ (для упоминания)
            attachment_ids: список UUID прикреплённых файлов (максимум 4)

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
        return await replies(
            self.client, self._access_token, comment_id, content, replay_to_user_id, attachment_ids,
            self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def edit_comment(
            self,
            comment_id: UUID,
            content: str,
            **kwargs
    ) -> UpdateCommentResponse:
        """Редактировать комментарий.

        Args:
            comment_id: UUID комментария
            content: новый текст комментария

        Returns:
            Обновлённый комментарий (содержит дату редактирования)

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: комментарий не найден
            ForbiddenError: нет прав на редактирование этого комментария
            ParamsValidationError: 1 <= len(content) <= 1_000
        """
        return await edit_comment(
            self.client, self._access_token, comment_id, content,
            self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def delete_comment(
            self,
            comment_id: UUID,
            **kwargs
    ) -> None:
        """Удалить комментарий.

        Args:
            comment_id: UUID комментария

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: комментарий не найден
            ForbiddenError: нет прав на удаление комментария
        """
        await delete_comment(
            self.client, self._access_token, comment_id,
            self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def restore_comment(
            self,
            comment_id: UUID,
            **kwargs
    ) -> None:
        """Восстановить удалённый комментарий.

        Args:
            comment_id: UUID комментария

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: комментарий не найден
            ForbiddenError: нет прав на восстановление комментария
        """
        await restore_comment(
            self.client, self._access_token, comment_id,
            self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def like_comment(
            self,
            comment_id: UUID,
            **kwargs
    ) -> int:
        """Поставить лайк на комментарий.

        Args:
            comment_id: UUID комментария

        Returns:
            Обновлённое количество лайков

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: комментарий не найден
        """
        return await like_comment(
            self.client, self._access_token, comment_id,
            self.domain, timeout=self.timeout, **kwargs
        )

    @auth_required
    async def unlike_comment(
            self,
            comment_id: UUID,
            **kwargs
    ) -> int:
        """Убрать лайк с комментария.

        Args:
            comment_id: UUID комментария

        Returns:
            Обновлённое количество лайков

        Raises:
            UnauthorizedError: ошибка авторизации
            NotFoundError: комментарий не найден
        """
        return await unlike_comment(
            self.client, self._access_token, comment_id,
            self.domain, timeout=self.timeout, **kwargs
        )

    @asynccontextmanager
    async def connect_notifications(
            self,
            **kwargs
    ) -> AsyncGenerator[AsyncIterator[ConnectedEvent | NotificationEvent | SSEEvent], None]:
        """Подключиться к SEE стриму уведомлений.

        Raises:
            SSEError: ошибка SSE

        Examples:
            ```python
            refresh_token = "ВАШ ТОКЕН"
            async with AsyncITDClient(refresh_token) as client:
                async with client.connect_notifications() as events:
                    async for event in events:
                        print(event)
                        break
            ```
        """
        if self.is_token_expired():
            await self._refresh_with_lock()
        async with connect_notifications(
                self.client, self._access_token, self.domain, timeout=self.timeout, **kwargs
        ) as events:
            yield events

    async def get_changelog(
            self,
            **kwargs
    ) -> list[Version]:
        """Получить чейнджлог."""
        return await get_changelog(self.client, self.domain, timeout=self.timeout, **kwargs)


__all__ = ['AsyncITDClient']
