from datetime import datetime
from json import JSONDecodeError
from typing import Callable, IO, Coroutine, Literal, NamedTuple, Any, AsyncGenerator, AsyncIterator
import time
import base64
import json
import re
from uuid import UUID
import mimetypes
import asyncio
from contextlib import asynccontextmanager

from aioitd.exceptions import UnauthorizedError, NotFoundError, InvalidPasswordError, ValidationError, ITDError, \
    itd_codes, TooLargeError, NotAllowedError, RateLimitError, TokenMissingError, ParamsValidationError, Error429, \
    GatewayTimeOutError

from aioitd import models
import httpx
import httpx_sse

from aioitd.models import datetime_to_itd_format


ITD_CEE_PING = 15

def decode_jwt_payload(jwt_token: str) -> dict[str, Any]:
    """Декодирует pyload jwt"""
    payload = jwt_token.split('.')[1]
    payload += '=' * ((4 - len(payload) % 4) % 4)
    decoded = base64.urlsafe_b64decode(payload).decode('utf-8')
    return json.loads(decoded)


def is_token_expired(access_token: str) -> bool:
    """Истёк ли `access_token`."""
    payload = decode_jwt_payload(access_token)
    return time.time() - 1 >= payload['exp']


def add_bearer(token: str):
    """Добавить Bearer к токену, если отсутствует."""
    if 'Bearer' not in token:
        return "Bearer " + token.strip()
    else:
        return token


def validate_limit(limit: int, min: int = 1, max: int = 50):
    if not (1 <= limit <= 50):
        raise ValidationError(ValidationError.code, f"limit должен быть больше от {min} до {max}")


def valid_hashtag_name(hashtag: str) -> bool:
    """Проверить хештег"""
    return bool(re.match(r'^[A-Za-zА-Яа-я\d_]+$', hashtag))


def verify_password(password: str) -> bool:
    """Проверить пароль. От 8 до 100 символов, содержит хотя бы одну букву, содержит хотя бы оду цифру."""
    return bool(8 <= len(password) <= 100 and re.search(r"[a-zA-Z]", password) and re.search(r"\d", password))


def valid_file_mimetype(path: str) -> bool:
    """Проверить тип файла. Изображение, видео или аудио."""
    mimetype, _ = mimetypes.guess_file_type(path)
    if mimetype is None:
        return True
    mimetype = mimetype.split('/')[0]
    return mimetype in ["video", 'image', 'audio']


class FetchInterval:
    """Рассчитывает задержку между запросами

    Attributes:
        time_delta: минимальная задержка между запросами
    """

    def __init__(self, time_delta: float | int = 0.105):
        self.time_delta = time_delta
        self.last_fetch = 0

    async def __call__(self):
        await self.interval()

    async def interval(self):
        t = time.time()
        last_fetch = self.last_fetch
        if t - last_fetch < self.time_delta:
            self.last_fetch = last_fetch + self.time_delta
            await asyncio.sleep(self.time_delta - t + last_fetch)
        self.last_fetch = time.time()


class AsyncITDClient:
    """
    Attributes:
        refresh_token: refresh token
        domain: домен
        refresh_on_unauthorized: для каждого запроса в случае `UnauthorizedError` вызвать `refresh` и сделать
            запрос ещё раз
        check_access_token_expired: проверять ли access токен. Если True перед каждым запросом токен будет проверен и
            в случае истечения времени жизни, будет вызван `refresh`
        upload_file_timeout: ограничение времени для загрузки файлов
        timeout: ограничение по времени для запросов
        time_delta: минимальная задержка между запросами, чтобы не возникало Error426. Используйте FetchInterval чтобы
            синхронизовать задержку между несколькими  AsyncITDClient. None чтобы отключить задержку
    """

    def __init__(
            self,
            refresh_token: str,
            domain: str = "xn--d1ah4a.com",
            refresh_on_unauthorized: bool = True,
            check_access_token_expired: bool = True,
            upload_file_timeout: int = 200,
            timeout: int = 10,
            time_delta: FetchInterval | float | int | None = 0.105
    ):
        if len(refresh_token) == 0:
            raise TokenMissingError(TokenMissingError.code, "refresh токен не может быть пустой строкой")
        self.refresh_token = refresh_token
        self.domain = domain
        self.access_token = "." + base64.urlsafe_b64encode(b'{"exp": 0}').decode("utf-8")
        self.check_access_token_expired = check_access_token_expired
        self.refresh_on_unauthorized = refresh_on_unauthorized
        self.session = httpx.AsyncClient()
        self.upload_file_timeout = upload_file_timeout
        self.timeout = timeout
        if isinstance(time_delta, FetchInterval):
            self.fetch_interval = time_delta
        elif time_delta is None:
            self.fetch_interval = None
        else:
            self.fetch_interval = FetchInterval(time_delta)

    async def __aenter__(self) -> AsyncITDClient:
        await self.start()
        return self

    async def start(self):
        pass

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def close(self) -> None:
        await self.session.aclose()

    async def _unauthorized_wrapper(self, method: Callable[..., Coroutine], url: str, **kwargs) -> httpx.Response:
        if self.check_access_token_expired:
            if is_token_expired(self.access_token):
                await self.refresh()

        if self.refresh_on_unauthorized:
            try:
                return await self._request(method, url, **kwargs)
            except UnauthorizedError:
                await self.refresh()
                return await self._request(method, url, **kwargs)
        else:
            return await self._request(method, url, **kwargs)

    async def _request(
            self,
            method: Callable[..., Coroutine[None, None, httpx.Response]],
            url: str, **kwargs
    ) -> httpx.Response:
        if kwargs.get("timeout") is None:
            kwargs["timeout"] = self.timeout

        if self.fetch_interval is not None:
            await self.fetch_interval()

        result = await method(
            f"https://{self.domain}/{url}",
            headers={"authorization": add_bearer(self.access_token)},
            **kwargs
        )

        if result.text == "UNAUTHORIZED":
            raise UnauthorizedError
        if result.text == "NOT_FOUND":
            raise NotFoundError
        if result.status_code == 413:
            raise TooLargeError(TooLargeError.code, "Размер запроса слишком большой")
        if result.status_code == 405:
            raise NotAllowedError(NotAllowedError.code, "Not Allowed")
        if result.status_code == 504:
            raise GatewayTimeOutError(GatewayTimeOutError.code, "504 Gateway Time-out")

        try:
            data = result.json()
            if 'type' in data:
                raise ParamsValidationError(type=data['type'], on=data['on'], found=data['found'])
            if 'error' in data:
                if data['error'] == 'Too Many Requests':
                    raise Error429(data['error'], data['message'])
                error = data['error']
                if error['code'] == "RATE_LIMIT_EXCEEDED":
                    raise RateLimitError(code=error['code'], message=error["message"], retry_after=error["retryAfter"])
                if error['code'] in itd_codes:
                    ex = itd_codes[error['code']]
                    message = ex.message if hasattr(ex, "message") else error['message']
                    raise ex(ex.code, message)
                else:
                    raise ITDError(code=error['code'], message=error["message"])
        except JSONDecodeError:
            if result.status_code != 204:
                raise ITDError("UNKNOWN", result.text)

        return result

    async def get(self, url: str, params: dict | None = None) -> httpx.Response:
        return await self._unauthorized_wrapper(self.session.get, url, params=params)

    async def post(self, url: str, json: Any | None = None, params: dict | None = None,
                   cookies: dict | None = None, files: dict | None = None,
                   timeout: int | None = None) -> httpx.Response:
        return await self._unauthorized_wrapper(self.session.post, url, json=json, params=params, cookies=cookies,
                                                files=files, timeout=timeout)

    async def delete(self, url: str, params: dict | None = None) -> httpx.Response:
        return await self._unauthorized_wrapper(self.session.delete, url, params=params)

    async def put(self, url: str, json: Any | None = None, params: dict | None = None) -> httpx.Response:
        return await self._unauthorized_wrapper(self.session.put, url, json=json, params=params)

    async def change_password(
            self,
            old_password: str,
            new_password: str,
    ) -> None:
        """Поменять пароль. При успешной смене пароля `refresh_token` отзывается.

        Args:
            old_password: старый пароль
            new_password: новый пароль

        Raises:
            InvalidPasswordError: Пароль не подходит под условия
            InvalidOldPasswordError: Указан неверный старый пароль
            SomePasswordError: Новый пароль должен отличать от старого
            UnauthorizedError: истёк access_token
        """
        if not verify_password(new_password):
            raise InvalidPasswordError(code=InvalidPasswordError.code, message='Password requirement not met')

        await self.post("api/v1/auth/change-password", {"oldPassword": old_password, "newPassword": new_password})

    async def logout(self) -> None:
        """Выйти из аккаунта, отозвать токен. Работает при любом токене. Просроченном, не существующем и пустой строкой тоже."""
        await self.post("https://xn--d1ah4a.com/api/v1/auth/logout", cookies={"refresh_token": self.refresh_token})

    async def refresh(self) -> str:
        """Получить access_token.

        Returns: access токен

        Raises:
            TokenNotFoundError: Такого токена не существует
            TokenRevokedError: Токен отозван
            TokenMissingError: Токен не указан (равен пустой строке)
        """
        if len(self.refresh_token) == 0:
            raise TokenMissingError(code=TokenMissingError.code, message="Refresh token not found")

        result = await self._request(
            self.session.post,
            "api/v1/auth/refresh",
            cookies={"refresh_token": self.refresh_token}
        )
        self.access_token = result.json()["accessToken"]
        return self.access_token

    async def upload_file(self, file: IO[bytes], validate_mimetype: bool = True) -> models.File:
        """Загрузить файл.

        Args:
            file: файл
            validate_mimetype: проверять ли тип файла перед запросом

        Raises:
            UnauthorizedError: неверный access токен
            ValidationError: недопустимый тип файла
            TooLargeError: размер запроса слишком большой
            UploadError: ошибка загрузки файла
        """
        if validate_mimetype and not valid_file_mimetype(file.name):
            raise ValidationError(ValidationError.code, 'Недопустимый тип файла')
        result = await self.post("api/files/upload", files={'file': file}, timeout=self.upload_file_timeout)
        return models.File(**result.json())

    async def get_file(self, file_id: UUID | str) -> models.GetFile:
        """Получить файл.

        Args:
            file_id: UUID файла

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: файл не найден
        """
        if isinstance(file_id, str):
            file_id = UUID(file_id)
        result = await self.get(f"api/files/{file_id}")
        return models.GetFile(**result.json())

    async def delete_file(self, file_id: UUID | str):
        """Удалить файл

        Args:
            file_id: UUID файла

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: Файл не найден, или нет прав доступа к нему
        """
        if isinstance(file_id, str):
            file_id = UUID(file_id)
        await self.delete(f"api/files/{file_id}")

    async def get_trending_hashtags(self, limit: int = 10) -> list[models.Hashtag]:
        """Получить популярные хештеги.

        Args:
            limit: максимальное количество выданных хештегов

        Raises:
            UnauthorizedError: неверный access токен
            ValidationError: 1 <= limit <= 50
        """
        validate_limit(limit)
        result = await self.get("api/hashtags/trending", params={"limit": limit})
        data = result.json()["data"]
        return list(map(lambda hashtag: models.Hashtag(**hashtag), data["hashtags"]))

    async def search_hashtags(self, query: str, limit: int = 20) -> list[models.Hashtag]:
        """Найти хештеги.

        Args:
            query: текст запроса
            limit: максимальное количество выданных хештегов

        Raises:
            UnauthorizedError: неверный access токен
            ValidationError: 1 <= limit <= 50
            ValidationError: len(query) <= 100
        """
        validate_limit(limit)
        if len(query) > 100:
            raise ValidationError(ValidationError.code, "Длина запроса должна быть не более 100")
        result = await self.get(f"api/hashtags", params={"q": query, "limit": limit})
        data = result.json()["data"]
        return list(map(lambda hashtag: models.Hashtag(**hashtag), data["hashtags"]))

    async def get_posts_by_hashtag(
            self, hashtag_name: str, cursor: UUID | str | None = None,
            limit: int = 20
    ) -> tuple[models.Hashtag, models.UUIDPagination, list[models.HashtagPost]]:
        """Посты по хештегу.

        Args:
            hashtag_name: текст хештега
            cursor: UUID последнего поста на прошлой странице
            limit: максимальное количество выданных постов

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: Хештег не найден
            ValidationError: 1 <= limit <= 50
        """
        validate_limit(limit)
        if isinstance(cursor, str):
            cursor = UUID(cursor)
        if len(hashtag_name) == 0:
            raise NotFoundError("NOT_FOUND", f"Хештег (пустая строка) не найден")

        try:
            result = await self.get(
                f"api/hashtags/{hashtag_name}/posts",
                params={"limit": limit} | ({} if cursor is None else {"cursor": str(cursor)})

            )
        except NotFoundError:
            raise NotFoundError("NOT_FOUND", f"Хештег {hashtag_name} не найден")

        data = result.json()["data"]
        hashtag = data["hashtag"]
        if hashtag is None:
            raise NotFoundError("NOT_FOUND", f"Хештег {hashtag_name} не найден")
        hashtag = models.Hashtag(**hashtag)

        pagination = models.UUIDPagination(**data["pagination"])

        posts = list(map(lambda post: models.HashtagPost(**post), data["posts"]))

        return hashtag, pagination, posts

    async def get_popular_posts(
            self,
            cursor: int | None = None,
            limit: int = 20
    ) -> tuple[models.IntPagination, list[models.PopularPost]]:
        """Получить популярные посты, лента.

        Args:
            cursor: Номер страницы
            limit: максимальное количество постов на странице

        Raises:
            UnauthorizedError: неверный access токен
            ValidationError: 1 <= limit <= 50
        """
        validate_limit(limit)

        result = await self.get(
            f"api/posts", params={"limit": limit, "tab": "popular"} | {} if cursor is None else {"cursor": cursor}
        )
        data = result.json()["data"]

        pagination = models.IntPagination(**data["pagination"])

        posts = list(map(lambda post: models.PopularPost(**post), data["posts"]))

        return pagination, posts

    async def get_following_posts(
            self, cursor: datetime | None = None, limit: int = 20
    ) -> tuple[models.TimePagination, list[models.Post]]:
        """Посты подписок

        Args:
            cursor: Дата создания последнего поста на предыдущей странице
            limit: максимальное количество постов на странице

        Raises:
            UnauthorizedError: неверный access токен
            ValidationError: 1 <= limit <= 50
        """
        validate_limit(limit)

        result = await self.get(
            f"api/posts",
            params={"limit": limit, "tab": "following"} | (
                {} if cursor is None else {"cursor": datetime_to_itd_format(cursor)})
        )
        data = result.json()["data"]

        pagination = models.TimePagination(**data["pagination"])

        posts = list(map(lambda post: models.Post(**post), data["posts"]))

        return pagination, posts

    async def get_post(self, post_id: UUID | str) -> models.FullPost:
        """Получить пост.

        Args:
            post_id: UUID поста

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: пост не существует, удалён, владелец поста забанил
        """
        if isinstance(post_id, str):
            post_id = UUID(post_id)

        result = await self.get(f"api/posts/{post_id}")

        return models.FullPost(**result.json()["data"])

    async def delete_post(self, post_id: UUID | str) -> None:
        """Удалить пост.

        Args:
            post_id: UUID поста

        Raises:
            UnauthorizedError: неверный access токен
            ForbiddenError: Нет прав для удаления поста
            NotFoundError: Пост не найден
        """

        if isinstance(post_id, str):
            post_id = UUID(post_id)

        await self.delete(f"api/posts/{post_id}")

    async def restore_post(self, post_id: UUID | str) -> None:
        """Восстановить пост.

        Args:
            post_id: UUID поста
        Raises:
            UnauthorizedError: неверный access токен
            ForbiddenError: Нет прав для восстановления поста
            NotFoundError: Пост не найден или удалён
        """
        if isinstance(post_id, str):
            post_id = UUID(post_id)

        await self.post(f"api/posts/{post_id}/restore")

    async def like_post(self, post_id: UUID | str) -> int:
        """Лайкнуть пост.

        Args:
            post_id: UUID поста

        Returns: Количество лайков

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: Пост не найден
        """
        if isinstance(post_id, str):
            post_id = UUID(post_id)

        result = await self.post(f"api/posts/{post_id}/like")
        return result.json()["likesCount"]

    async def delete_like_post(self, post_id: UUID | str) -> int:
        """Убрать лайк с пост.

        Args:
            post_id: UUID поста

        Returns: Количество лайков

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: Пост не найден
        """
        if isinstance(post_id, str):
            post_id = UUID(post_id)

        result = await self.delete(f"api/posts/{post_id}/like")
        return result.json()["likesCount"]

    async def view_post(self, post_id: UUID | str) -> None:
        """Просмотр на пост.

        Args:
            post_id: UUID поста

        Raises:
            UnauthorizedError: неверный access токен
        """
        if isinstance(post_id, str):
            post_id = UUID(post_id)

        await self.post(f"api/posts/{post_id}/view")

    async def pin_post(self, post_id: UUID | str) -> bool:
        """Закрепить пост.

        Args:
            post_id: UUID поста

        Returns: Успешна ли операция

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: Пост не найден
            ForbiddenError: Можно прикреплять посты только на своей стене
        """
        if isinstance(post_id, str):
            post_id = UUID(post_id)

        result = await self.post(f"api/posts/{post_id}/pin")
        return result.json()["success"]

    async def unpin_post(self, post_id: UUID | str) -> bool:
        """Открепить пост.

        Args:
            post_id: UUID поста

        Returns: Успешна ли операция

        Raises:
            UnauthorizedError: неверный access токен
            NotPinedError: Пост не прикреплён
        """
        if isinstance(post_id, str):
            post_id = UUID(post_id)

        result = await self.delete(f"api/posts/{post_id}/pin")
        return result.json()["success"]

    async def repost(self, post_id: UUID | str, content: str = "") -> models.PostWithoutAuthorId:
        """Репост.

        Args:
            post_id: UUID поста
            content: текст репоста

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: Пост не найден
            ConflictError: Нельзя репостнуть два раза
            ValidationError: Нельзя репостить свои посты
            ValidationError: len(content) <= 5_000
        """
        if isinstance(post_id, str):
            post_id = UUID(post_id)
        if len(content) > 5_000:
            raise ValidationError(ValidationError.code, "Максимальная длина content 5_000")

        result = await self.post(f"api/posts/{post_id}/repost", json={"content": content})
        data = result.json()
        return models.PostWithoutAuthorId(**data)

    async def get_posts_by_user(
            self, username: str, cursor: str | None = None, limit: int = 20, sort: Literal["new", "popular"] = "new"
    ) -> tuple[models.Pagination, list[models.UserPost]]:
        """Посты на стене пользователя.

                Args:
                    username: имя пользователя
                    cursor: next_cursor на предыдущей странице
                    limit: максимальное количество выданных постов
                    sort: сортировка

                Raises:
                    UnauthorizedError: неверный access токен
                    NotFoundError: пользователь не найден
                    ValidationError: 1 <= limit <= 50
                """
        validate_limit(limit)
        if len(username) == 0:
            raise NotFoundError(NotFoundError.code, 'User not found')
        result = await self.get(
            f"api/posts/user/{username}",
            params={"sort": sort, "limit": limit} | (
                {} if cursor is None else {"cursor": cursor})
        )
        data = result.json()["data"]
        pagination = models.Pagination(**data["pagination"])
        posts = list(map(lambda post: models.UserPost(**post), data["posts"]))

        return pagination, posts

    async def get_posts_by_user_newest(
            self, username: str, cursor: datetime | None = None, limit: int = 20
    ) -> tuple[models.TimePagination, list[models.UserPost]]:
        """Посты на стене пользователя. Отсортированы по дате публикации

        Args:
            username: имя пользователя
            cursor: время публикации последнего поста на предыдущей странице
            limit: максимальное количество выданных постов

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: пользователь не найден
            ValidationError: 1 <= limit <= 50
        """
        validate_limit(limit)
        if len(username) == 0:
            raise NotFoundError(NotFoundError.code, 'User not found')
        result = await self.get(
            f"api/posts/user/{username}",
            params={"sort": "new", "limit": limit} | (
                {} if cursor is None else {"cursor": datetime_to_itd_format(cursor)})
        )
        data = result.json()["data"]
        pagination = models.TimePagination(**data["pagination"])
        posts = list(map(lambda post: models.UserPost(**post), data["posts"]))

        return pagination, posts

    async def get_posts_by_user_popular(
            self, username: str, cursor: int | None = None, limit: int = 20
    ) -> tuple[models.IntPagination, list[models.UserPost]]:
        """Посты на стене пользователя. Отсортированы по популярности.

        Args:
            username: имя пользователя
            cursor: номер последнего поста на предыдущей странице
            limit: максимальное количество выданных постов

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: пользователь не найден
            ValidationError: 1 <= limit <= 50
        """
        validate_limit(limit)
        if len(username) == 0:
            raise NotFoundError(NotFoundError.code, 'User not found')
        result = await self.get(
            f"api/posts/user/{username}",
            params={"sort": "popular", "limit": limit} | ({} if cursor is None else {"cursor": str(cursor)})
        )
        data = result.json()["data"]
        pagination = models.IntPagination(**data["pagination"])
        posts = list(map(lambda post: models.UserPost(**post), data["posts"]))

        return pagination, posts

    async def get_posts_by_user_liked(
            self, username: str, cursor: datetime | None = None, limit: int = 20
    ) -> tuple[models.TimePagination, list[models.Post]]:
        """Посты на которые пользователей поставил лайк.

        Args:
            username: имя пользователя
            cursor: время публикации последнего поста на предыдущей странице
            limit: максимальное количество выданных постов

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: пользователь не найден
            ValidationError: 1 <= limit <= 50
        """
        validate_limit(limit)
        if len(username) == 0:
            raise NotFoundError(NotFoundError.code, 'User not found')
        result = await self.get(
            f"api/posts/user/{username}/liked",
            params={"sort": "new", "limit": limit} | (
                {} if cursor is None else {"cursor": datetime_to_itd_format(cursor)})
        )
        data = result.json()["data"]
        pagination = models.TimePagination(**data["pagination"])
        posts = list(map(lambda post: models.Post(**post), data["posts"]))

        return pagination, posts

    async def get_posts_by_user_wall(
            self, username: str, cursor: datetime | None = None, limit: int = 20
    ) -> tuple[models.TimePagination, list[models.UserPost]]:
        """Посты на стене пользователя, сделанные не пользователем.

        Args:
            username: имя пользователя
            cursor: время публикации последнего поста на предыдущей странице
            limit: максимальное количество выданных постов

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: пользователь не найден
            ValidationError: 1 <= limit <= 50
        """
        validate_limit(limit)
        if len(username) == 0:
            raise NotFoundError(NotFoundError.code, 'User not found')
        result = await self.get(
            f"api/posts/user/{username}/wall",
            params={"sort": "new", "limit": limit} | (
                {} if cursor is None else {"cursor": datetime_to_itd_format(cursor)})
        )
        data = result.json()["data"]
        pagination = models.TimePagination(**data["pagination"])
        posts = list(map(lambda post: models.UserPost(**post), data["posts"]))

        return pagination, posts

    async def get_post_comments(
            self,
            post_id: UUID | str,
            cursor: str | None = None,
            sort: Literal["popular", "newest", "oldest"] = "popular",
            limit: int = 20
    ) -> tuple[models.CommentPagination, list[models.Comment]]:
        """Получить комментарии под постом.

        Args:
            post_id: UUID поста
            cursor: next_cursor с предыдущей страницы
            sort: сортировать по
            limit: максимальное количество комментариев на странице

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: Пост не найден
            ValidationError: 1 <= limit <= 50
        """
        validate_limit(limit)
        if isinstance(post_id, str):
            post_id = UUID(post_id)
        result = await self.get(
            f"api/posts/{post_id}/comments",
            params={"sort": sort, "limit": limit} | ({} if cursor is None else {"cursor": cursor})
        )
        data = result.json()["data"]
        comments = list(map(lambda comment: models.Comment(**comment), data["comments"]))
        del data['comments']
        pagination = models.CommentPagination(**data)
        return pagination, comments

    async def get_post_popular_comments(
            self,
            post_id: UUID | str,
            cursor: int | None = None,
            limit: int = 20
    ) -> tuple[models.IntCommentPagination, list[models.Comment]]:
        """Получить популярные комментарии под постом.

        Args:
            post_id: UUID поста
            cursor: номер последнего комментария на предыдущей странице
            limit: максимальное количество комментариев на странице

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: Пост не найден
            ValidationError: 1 <= limit <= 50
        """
        validate_limit(limit)
        if isinstance(post_id, str):
            post_id = UUID(post_id)
        result = await self.get(
            f"api/posts/{post_id}/comments",
            params={"sort": "popular", "limit": limit} | ({} if cursor is None else {"cursor": str(cursor)})
        )
        data = result.json()["data"]
        comments = list(map(lambda comment: models.Comment(**comment), data["comments"]))
        del data['comments']
        pagination = models.IntCommentPagination(**data)
        return pagination, comments

    async def get_post_newest_comments(
            self,
            post_id: UUID | str,
            cursor: UUID | str | None = None,
            limit: int = 20
    ) -> tuple[models.UUIDCommentPagination, list[models.Comment]]:
        """Получить новые комментарии под постом.

        Args:
            post_id: UUID поста
            cursor: UUID последнего комментария на предыдущей странице
            limit: максимальное количество комментариев на странице

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: Пост не найден
            ValidationError: 1 <= limit <= 50
        """
        validate_limit(limit)
        if isinstance(post_id, str):
            post_id = UUID(post_id)
        if isinstance(cursor, str):
            cursor = UUID(cursor)
        result = await self.get(
            f"api/posts/{post_id}/comments",
            params={"sort": "newest", "limit": limit} | ({} if cursor is None else {"cursor": str(cursor)})
        )
        data = result.json()["data"]
        comments = list(map(lambda comment: models.Comment(**comment), data["comments"]))
        del data['comments']
        pagination = models.UUIDCommentPagination(**data)
        return pagination, comments

    async def get_post_oldest_comments(
            self,
            post_id: UUID | str,
            cursor: UUID | str | None = None,
            limit: int = 20
    ) -> tuple[models.UUIDCommentPagination, list[models.Comment]]:
        """Получить старые комментарии под постом.

        Args:
            post_id: UUID поста
            cursor: UUID последнего комментария на предыдущей странице
            limit: максимальное количество комментариев на странице

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: Пост не найден
            ValidationError: 1 <= limit <= 50
        """
        validate_limit(limit)
        if isinstance(post_id, str):
            post_id = UUID(post_id)
        if isinstance(cursor, str):
            cursor = UUID(cursor)
        result = await self.get(
            f"api/posts/{post_id}/comments",
            params={"sort": "oldest", "limit": limit} | ({} if cursor is None else {"cursor": str(cursor)})
        )
        data = result.json()["data"]
        comments = list(map(lambda comment: models.Comment(**comment), data["comments"]))
        del data['comments']
        pagination = models.UUIDCommentPagination(**data)
        return pagination, comments

    async def create_post(
            self,
            content: str,
            attachment_ids: list[UUID | str] | None = None,
            wall_recipient_id: UUID | str = None
    ) -> models.UserPostWithoutAuthorId:
        """Создать пост.

        Args:
            content: Текст поста
            attachment_ids: Прикреплённые файлы
            wall_recipient_id: id пользователя
        Raises:
            UnauthorizedError: неверный access токен
            ValidationError: len(content) <= 5_000
            ValidationError: len(attachments_ids) <= 10
            ValidationError: Нельзя создать пост content="", attachment_ids = []
            NotFoundError: пользователь не найден
        """
        if len(content) > 5_000:
            raise ValidationError(ValidationError.code, "Максимальная длина content 5_000")
        if attachment_ids is None:
            attachment_ids = []
        elif len(attachment_ids) > 10:
            raise ValidationError(ValidationError.code, 'Maximum 10 attachments allowed per post')
        else:
            attachment_ids = list(map(lambda id: UUID(id) if isinstance(id, str) else id, attachment_ids))
        if len(attachment_ids) == 0 and len(content) == 0:
            raise ValidationError(ValidationError.code, 'Content or attachments required')
        result = await self.post(
            "api/posts",
            {
                "content": content,
                "attachmentIds": list(map(str, attachment_ids))} |
            ({} if wall_recipient_id is None else {"wallRecipientId": str(wall_recipient_id)})
        )
        data = result.json()

        return models.UserPostWithoutAuthorId(**data)

    async def update_post(self, post_id: UUID | str, content: str) -> models.UpdatePostResponse:
        """Изменить пост

        Args:
            post_id: UUID поста
            content: Новый текст поста

        Returns: Новое содержимое поста

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: Пост не найден
            ValidationError: 1 <= len(content) <= 5_000
            ForbiddenError: Нет прав для редактирования этого поста
        """
        if isinstance(post_id, str):
            post_id = UUID(post_id)
        if len(content) > 5_000 or len(content) == 0:
            raise ValidationError(ValidationError.code, "Максимальная длина content 5_000, минимальная 0")

        result = await self.put(f"api/posts/{post_id}", {"content": content})
        data = result.json()

        return models.UpdatePostResponse(**data)

    async def comment(
            self, post_id: UUID | str, content: str = "", attachment_ids: list[UUID | str] | None = None
    ) -> models.BaseComment:
        """Создать комментарий.

        Args:
            post_id: UUID поста
            content: текст поста
            attachment_ids: список UUID файлов

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: пост не найден
            ValidationError: len(content) <= 5_000
            ValidationError: len(attachments_ids) <= 4
            ValidationError: Нельзя создать пост content="", attachment_ids = []
        """
        if len(content) > 5_000:
            raise ValidationError(ValidationError.code, "Максимальная длина content 5_000")
        if isinstance(post_id, str):
            post_id = UUID(post_id)
        if attachment_ids is None:
            attachment_ids = []
        elif len(attachment_ids) > 4:
            raise ValidationError(ValidationError.code, 'Maximum 10 attachments allowed per post')
        else:
            attachment_ids = list(map(lambda id: UUID(id) if isinstance(id, str) else id, attachment_ids))
        result = await self.post(
            f"api/posts/{post_id}/comments",
            {"content": content, "attachmentIds": list(map(str, attachment_ids))}
        )
        data = result.json()
        return models.BaseComment(**data)

    async def delete_comment(self, comment_id: UUID | str) -> None:
        """Удалить комментарий.

        Args:
            comment_id: UUID комментария

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: комментарий не найден
            ForbiddenError: нет прав на удаление комментария
        """
        if isinstance(comment_id, str):
            comment_id = UUID(comment_id)

        await self.delete(f"api/comments/{comment_id}")

    async def restore_comment(self, comment_id: UUID | str) -> None:
        """Восстановить комментарий.

        Args:
            comment_id: UUID комментария

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: комментарий не найден
        """
        if isinstance(comment_id, str):
            comment_id = UUID(comment_id)
        await self.post(f"api/comments/{comment_id}/restore")

    async def like_comment(self, comment_id: UUID | str) -> int:
        """Поставить лайк на комментарий.

        Args:
            comment_id: UUID комментария

        Returns: Количество лайков на комментарии

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: комментарий не найден
        """
        if isinstance(comment_id, str):
            comment_id = UUID(comment_id)
        result = await self.post(f"api/comments/{comment_id}/like")
        return result.json()["likesCount"]

    async def delete_like_comment(self, comment_id: UUID | str) -> int:
        """Удалить лайк с комментария.

        Args:
            comment_id: UUID комментария

        Returns: Количество лайков на комментарии

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: комментарий не найден
        """
        if isinstance(comment_id, str):
            comment_id = UUID(comment_id)
        result = await self.delete(f"api/comments/{comment_id}/like")
        return result.json()["likesCount"]

    async def replies(
            self,
            comment_id: UUID | str,
            content: str,
            replay_to_user_id: UUID | str | None = None,
            attachment_ids: list[UUID | str] | None = None
    ) -> models.ReplyComment:
        """Ответить на комментарий

        Args:
            comment_id: UUID комментария
            content: текст ответа
            replay_to_user_id: UUID пользователя, которому ответ
            attachment_ids: список UUID файлов

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: комментарий не найден
            ValidationError: len(content) <= 5_000
            ValidationError: len(attachments_ids) <= 4
            ValidationError: Нельзя создать ответ content="", attachment_ids = []
        """
        if len(content) > 5_000:
            raise ValidationError(ValidationError.code, "Максимальная длина content 5_000")
        if attachment_ids is None:
            attachment_ids = []
        elif len(attachment_ids) > 4:
            raise ValidationError(ValidationError.code, 'Maximum 10 attachments allowed per post')
        else:
            attachment_ids = list(map(lambda id: UUID(id) if isinstance(id, str) else id, attachment_ids))
        if len(attachment_ids) == 0 and len(content) == 0:
            raise ValidationError(ValidationError.code, 'Content or attachments required')

        if isinstance(comment_id, str):
            comment_id = UUID(comment_id)

        result = await self.post(
            f"api/comments/{comment_id}/replies",
            {"content": content, "attachmentIds": list(map(str, attachment_ids))}
            | ({} if replay_to_user_id is None else {"replayToUserId": str(replay_to_user_id)})
        )
        data = result.json()
        return models.ReplyComment(**data)

    async def search(
            self,
            query: str,
            user_limit: int = 20,
            hashtag_limit: int = 20
    ) -> tuple[list[models.Hashtag], list[models.User]]:
        """Поиск

        Args:
            query: запрос
            user_limit: максимальное количество выданных пользователей
            hashtag_limit: максимальное количество выданных хештегов
        Raises:
            UnauthorizedError: неверный access токен
            ValidationError: 1 <= limit <= 20
        """
        validate_limit(user_limit, 1, 20)
        validate_limit(hashtag_limit, 1, 20)
        result = await self.get(
            "api/search/", params={"userLimit": user_limit, "hashtagsLimit": hashtag_limit, 'q': query}
        )

        data = result.json()["data"]

        hashtags = list(map(lambda hashtag: models.Hashtag(**hashtag), data["hashtags"]))
        users = list(map(lambda user: models.User(**user), data["users"]))

        return users, hashtags

    async def search_users2(self, query: str, user_limit: int = 20) -> list[models.User]:
        """Поиск пользователей

        Args:
            query: запрос
            user_limit: максимальное количество выданных пользователей

        Raises:
            UnauthorizedError: неверный access токен
            ValidationError: 1 <= limit <= 20
        """
        validate_limit(user_limit, 1, 20)
        result = await self.get(
            "api/search/", params={"userLimit": user_limit, 'q': query}
        )
        data = result.json()["data"]

        users = list(map(lambda user: models.User(**user), data["users"]))

        return users

    async def search_hashtags2(self, query: str, hashtag_limit: int = 20) -> list[models.Hashtag]:
        """Поиск хештегов

        Args:
            query: запрос
            hashtag_limit: максимальное количество выданных хештегов

        Raises:
            UnauthorizedError: неверный access токен
            ValidationError: 1 <= limit <= 20
        """
        validate_limit(hashtag_limit, 1, 20)
        result = await self.get(
            "api/search/", params={"hashtagLimit": hashtag_limit, 'q': query}
        )
        data = result.json()["data"]

        users = list(map(lambda hashtag: models.Hashtag(**hashtag), data["hashtags"]))

        return users

    async def report(
            self,
            target_id: UUID | str,
            target_type: Literal["post", "comment", "user"] = "user",
            reason: Literal["spam", "violence", "hate", "adult", "fraud", "other"] = "other",
            description: str = "",
    ) -> models.Report:
        """Отправить репорт.

        Args:
            target_id: UUID цели
            target_type: тип цели
            reason: причина
            description: текст репорта
        """
        if isinstance(target_id, str):
            target_id = UUID(target_id)
        result = await self.post(
            "api/reports",
            {"targetId": str(target_id), "targetType": target_type, "reason": reason, "description": description}
        )
        data = result.json()["data"]
        return models.Report(**data)

    async def update_profile(
            self,
            bio: str | None = None,
            display_name: str | None = None,
            username: str | None = None,
            banner_id: UUID | str | None = None
    ) -> models.Me:
        """Обновить профиль.

        Args:
            bio: о себе
            display_name: имя
            username: имя пользователя
            banner_id: UUID файла, для нового баннера
        """
        if isinstance(banner_id, str):
            banner_id = UUID(banner_id)
        json = {}
        if bio is not None:
            json["bio"] = bio
        if display_name is not None:
            json["displayName"] = display_name
        if username is not None:
            json["username"] = username
        if banner_id is not None:
            json['bannerId'] = str(banner_id)

        result = await self.put("api/users/me", json)
        data = result.json()
        return models.Me(**data)

    async def get_user(self, username: str) -> models.FullUser | models.BlockedUser | models.UserBlockMe:
        """Получить данные пользователя.

        Args:
            username: имя пользователя
        """
        result = await self.get(f"api/users/{username}")
        data = result.json()
        if 'isBlockedByMe' in data:
            return models.BlockedUser(**data)
        elif 'isBlockedByThem' in data:
            return models.UserBlockMe(**data)
        else:
            return models.FullUser(**data)

    async def get_me(self) -> models.FullMe:
        """Получить данные текущего пользователя"""
        result = await self.get(f"api/users/me")
        data = result.json()
        return models.FullMe(**data)

    async def follow(self, username: str) -> int:
        """Подписаться на пользователя

        Args:
            username: имя пользователя

        Returns: Количество подписчиков пользователя
        """
        result = await self.post(f"api/users/{username}/follow")
        return result.json()["followersCount"]

    async def unfollow(self, username: str) -> int:
        """Отписать от пользователя

        Args:
            username: имя пользователя

        Returns: Количество подписчиков пользователя
        """
        result = await self.post(f"api/users/{username}/follow")
        return result.json()["followersCount"]

    async def get_followers(
            self,
            username: str,
            page: int = 1,
            limit: int = 30
    ) -> tuple[models.FollowPagination, list[models.FollowUser]]:
        """Получить подписчиков пользователя.

        Args:
            username: имя пользователя
            page: страница
            limit: максимальное количество пользователей на странице
        """
        result = await self.get(f"api/users/{username}/followers", params={"limit": limit, "page": page})
        data = result.json()["data"]
        pagination = models.FollowPagination(**data['pagination'])
        users = list(map(lambda user: models.FollowUser(**user), data["users"]))

        return pagination, users

    async def get_following(
            self,
            username: str,
            page: int = 1,
            limit: int = 30
    ) -> tuple[models.FollowPagination, list[models.FollowUser]]:
        """Получить подписки пользователя.

        Args:
            username: имя пользователя
            page: страница
            limit: максимальное количество пользователей на странице
        """
        result = await self.get(f"api/users/{username}/following", params={"limit": limit, "page": page})
        data = result.json()["data"]
        pagination = models.FollowPagination(**data['pagination'])
        users = list(map(lambda user: models.FollowUser(**user), data["users"]))

        return pagination, users

    async def get_top_clans(self) -> list[models.Clan]:
        """Получить топ кланов."""
        result = await self.get('api/users/stats/top-clans')
        data = result.json()
        return list(map(lambda clan: models.Clan(**clan), data["clans"]))

    async def get_who_to_follow(self) -> list[models.User]:
        """Получить топ по подпискам."""
        result = await self.get('api/users/suggestions/who-to-follow')
        data = result.json()
        return list(map(lambda user: models.User(**user), data["users"]))

    class NotificationsResponse(NamedTuple):
        has_more: bool
        notifications: list[models.Notification]

    async def get_notifications(self, offset: int = 0, limit: int = 30) -> NotificationsResponse:
        """Получить уведомления.

        Args:
            offset: сдвиг
            limit: максимально количество уведомлений в ответе
        """
        result = await self.get("api/notifications/", params={"limit": limit, "offset": offset})
        data = result.json()
        return self.NotificationsResponse(
            data["hasMore"],
            list(map(lambda notification: models.Notification(**notification), data["notifications"]))
        )

    async def read_batch_notifications(self, notifications_ids: list[UUID | str]) -> int:
        """Пометить прочитанными несколько уведомлений.

        Args:
            notifications_ids: список UUID уведомлений
        """
        notifications_ids = list(map(lambda id: UUID(id) if isinstance(id, str) else id, notifications_ids))
        result = await self.post("api/notifications/read-batch", {"ids": list(map(str, notifications_ids))})
        return result.json()["count"]

    async def read_notification(self, notification_id: UUID | str) -> bool:
        """Пометить сообщение прочитанным.

        Args:
            notification_id: UUID уведомления

        Returns: успешна ли операция
        """
        if isinstance(notification_id, str):
            notification_id = UUID(notification_id)
        result = await self.post(f"api/notifications/{notification_id}/read")
        return result.json()["success"]

    async def get_notifications_count(self) -> int:
        """Получить количество непрочитанных уведомлений"""
        result = await self.get("api/notifications/count")
        return result.json()["count"]

    async def read_all_notifications(self) -> bool:
        """Пометить все уведомления прочитанными.

        Returns: успешна ли операция
        """
        result = await self.post("api/notifications/read-all")
        return result.json()["success"]

    async def get_verification_status(self) -> str:
        """Получить статус верификации"""
        result = await self.get("api/verification/status")
        return result.json()["status"]

    async def submit_verification(self, video_url: str) -> dict:
        """Отправить запрос на верификацию.

        Args:
            video_url: url видео, загруженного на itd
        """
        result = await self.post("api/verification/submit", {"videoUrl": video_url})
        return result.json()

    async def search_users(self, query: str, limit: int = 20) -> list[models.User]:
        """Поиск пользователей.

        Args:
            query: текст запроса
            limit: максимальное количество выданных пользователей
        Raises:
            UnauthorizedError: неверный access токен
            ValidationError: 1 <= limit <= 50
        """
        validate_limit(limit)
        result = await self.get(f"api/users/search", params={"q": query, "limit": limit})
        data = result.json()["data"]

        return list(map(lambda user: models.User(**user), data['users']))

    class PinsResponse(NamedTuple):
        active_pin: str | None
        pins: list[models.PinWithDate]

    async def get_pins(self) -> PinsResponse:
        """Получить список пин'ов и текущий пин"""
        result = await self.get("api/users/me/pins")
        data = result.json()["data"]
        return self.PinsResponse(data['activePin'], list(map(lambda pin: models.PinWithDate(**pin), data["pins"])))

    async def set_pin(self, pin_slug: str) -> str:
        """Выбрать пин

        Args:
            pin_slug: slug пина

        Returns: slug пина
        """
        result = await self.put("api/users/me/pin", {"slug": pin_slug})
        return result.json()["pin"]

    async def delete_pin(self) -> None:
        """Убрать пин."""
        await self.delete("api/users/me/pin")

    async def get_privacy(self) -> models.Privacy:
        """Получить настройки приватности текущего пользователя."""
        result = await self.get(f"api/users/me/privacy")
        data = result.json()
        return models.Privacy(**data)

    async def update_privacy(
            self,
            is_private: bool | None = None,
            likes_visibility: Literal["everyone", "followers", "mutual", "nobody"] | None = None,
            wall_access: Literal["everyone", "followers", "mutual", "nobody"] | None = None
    ) -> models.Privacy:
        """Изменить настройки приватности текущего пользователя."""
        params = {}
        if is_private is not None:
            params["isPrivate"] = is_private
        if likes_visibility is not None:
            params["likesVisibility"] = likes_visibility
        if wall_access is not None:
            params["wallAccess"] = wall_access

        result = await self.put(f"api/users/me/privacy", params)
        data = result.json()
        return models.Privacy(**data)

    async def get_profile(self) -> models.Profile:
        """Получить свой профиль."""
        result = await self.get("api/profile")
        return models.Profile(**result.json())

    async def block(self, username: str):
        """Заблокировать пользователя."""
        await self.post(f"api/users/{username}/block")

    async def unblock(self, username: str):
        """Разблокировать пользователя."""
        await self.delete(f"api/users/{username}/block")

    async def get_blocked(
            self, page: int = 1, limit: int = 20
    ) -> tuple[models.FollowPagination, list[models.BlockedAuthor]]:
        """Получить заблокированных пользователей"""
        result = await self.get("api/users/me/blocked", {"page": page, "limit": limit})
        data = result.json()["data"]
        pagination = models.FollowPagination(**data["pagination"])
        users = list(map(lambda user: models.BlockedAuthor(**user), data["users"]))
        return pagination, users

    @staticmethod
    async def _sse_wrapper(
            aiter_see: Callable[[], AsyncGenerator[httpx_sse.ServerSentEvent, None]]
    ) -> AsyncGenerator[models.ConnectedEvent | models.NotificationEvent | models.SSEEvent, None]:
        async for sse in aiter_see():
            if sse.event == "connected":
                event = models.ConnectedEvent(**json.loads(sse.data))
            elif sse.event == "notification":
                event = models.NotificationEvent(**json.loads(sse.data))
            else:
                event = models.SSEEvent(event=sse.event, data=sse.data)
            yield event

    @asynccontextmanager
    async def connect_sse(
            self
    ) -> AsyncGenerator[AsyncGenerator[models.ConnectedEvent | models.NotificationEvent | models.SSEEvent, None], None]:
        """Подключиться к SEE стриму.

        Raises:
            SSEError: ошибка SSE
        """
        if is_token_expired(self.access_token):
            await self.refresh()

        async with httpx_sse.aconnect_sse(
                self.session, "GET", f"https://{self.domain}/api/notifications/stream",
                headers={"authorization": add_bearer(self.access_token)},
                timeout=ITD_CEE_PING + 1
        ) as event_source:
            try:
                yield self._sse_wrapper(event_source.aiter_sse)
            finally:
                pass
