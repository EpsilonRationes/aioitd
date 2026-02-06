from dataclasses import dataclass, field
from datetime import datetime
from json import JSONDecodeError
from typing import Any, Callable, IO, Coroutine
import time
import base64
import json
import re
from uuid import UUID

import httpx


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


def validate_limit(limit: int):
    if not (1 <= limit <= 50):
        raise ValueError("limit должен быть больше от 1 до 50")


class TokenNotFoundError(ValueError):
    def __init__(self, token: str) -> None:
        self.token = token

    def __str__(self):
        return f"Токена {self.token} не существует"


class TokenRevokedError(ValueError):
    def __init__(self, token: str) -> None:
        self.token = token

    def __str__(self) -> str:
        return f"Токен {self.token} отозван"


class MissingTokenError(ValueError):
    def __str__(self) -> str:
        return f"Токен не указан (равен пустой строке)"


class ITDError(Exception):
    def __init__(self, code: str, message: str):
        self.message = message
        self.code = code

    def __str__(self):
        return f"ITDError: code={self.code}, message={self.message}"


class UnauthorizedError(ITDError):
    def __str__(self):
        return f"Не авторизован"


class NotFoundError(ITDError):
    ...


class InvalidPasswordError(ValueError):
    def __str__(self) -> str:
        return "Пароль не подходит под условия"


class InvalidOldPasswordError(ValueError):
    def __str__(self) -> str:
        return "Указан неверный старый пароль"


class SomePasswordError(ValueError):
    def __str__(self) -> str:
        return "Новый пароль должен отличать от старого"


class FileNotFound(ValueError):
    def __str__(self):
        return f"Файл не найден, или нет прав доступа к нему"


def verify_password(password: str) -> bool:
    """Проверить пароль. От 8 до 100 символов, содержит хотя бы одну букву, содержит хотя бы оду цифру."""
    return 8 <= len(password) <= 100 and re.match(r"[a-zA-Z]", password) and re.match(r"\d", password)


@dataclass
class Pagination:
    """Пагинация.

    Attributes:
        has_more: есть ли следующая страница
        limit: максимальное количество постов на одной странице
    """
    has_more: bool
    limit: int

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Pagination:
        return Pagination(
            has_more=data["hasMore"],
            limit=data["limit"]
        )


@dataclass
class File:
    """Файл ИТД.

    Attributes:
        id: UUID файла
        filename: имя файла
        url: адрес файла
        mime_type: mime тип (https://developer.mozilla.org/ru/docs/Web/HTTP/Guides/MIME_types)
        size: размер файла в байтах
        created_at: время загрузки
    """
    id: UUID
    filename: str
    url: str
    mime_type: str
    size: int
    created_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> File:
        return File(
            id=UUID(data['id']),
            filename=data['filename'],
            url=data['url'],
            mime_type=data['mimeType'],
            size=data['size'],
            created_at=datetime.fromisoformat(data['createdAt'].replace('Z', '+00:00')) if data.get('createdAt')
            else datetime.now()
        )


@dataclass
class HashTag:
    """Хештег.

    Attributes:
        id: UUID хештега
        name: текст хештега
        posts_count: количество хештегов
    """
    id: UUID
    name: str
    posts_count: int

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> HashTag:
        return HashTag(
            id=UUID(data["id"]),
            name=data["name"],
            posts_count=data["postsCount"]
        )

@dataclass
class HashtagsPagination(Pagination):
    """Пагинация постов при поиске по хештегу

    Attributes:
        next_cursor: UUID последнего поста на странице
    """
    next_cursor: UUID

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> HashtagsPagination:
        pagination = super().from_json(data)
        return HashtagsPagination(
            **pagination.__dict__,
            next_cursor=UUID(data["nextCursor"])
        )

class ITDClient:
    """
    Attributes:
        refresh_token: refresh token
        domain: домен
        refresh_on_unauthorized: для каждого запроса в случае `UnauthorizedError` вызвать `refresh` и сделать
            запрос ещё раз
        check_access_token_expired: проверять ли access токен. Если True перед каждым запросом токен будет проверен и
            в случае истечения времени жизни, будет вызван `refresh`
    """

    def __init__(self, refresh_token: str, domain: str = "xn--d1ah4a.com", refresh_on_unauthorized: bool = True,
                 check_access_token_expired: bool = True):
        if len(refresh_token) == 0:
            raise ValueError("refresh токен не может быть пустой строкой")
        self.refresh_token = refresh_token
        self.domain = domain
        self.access_token = "." + base64.urlsafe_b64encode(b'{"exp": 0}').decode("utf-8")
        self.check_access_token_expired = check_access_token_expired
        self.refresh_on_unauthorized = refresh_on_unauthorized
        self.session = httpx.AsyncClient()

    async def __aenter__(self) -> ITDClient:
        await self.refresh()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def close(self) -> None:
        await self.session.aclose()


    def refresh_on_token_expired(func: Callable[..., Coroutine]) -> Callable[..., Coroutine]:
        async def wrapper(self: ITDClient, *args, **kwargs):
            if self.check_access_token_expired:
                if is_token_expired(self.access_token):
                    await self.refresh()
            if self.refresh_on_unauthorized:
                try:
                    return await func(*args, *kwargs)
                except UnauthorizedError:
                    await self.refresh()
                    return await func(*args, **kwargs)
            else:
                return await func(*args, **kwargs)

        return wrapper

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


    async def _request(self, method: Callable[..., Coroutine], url: str, **kwargs) -> httpx.Response:
        result = await method(
            f"https://{self.domain}/{url}",
            headers={"authorization": add_bearer(self.access_token)},
            **kwargs
        )

        if result.text == "UNAUTHORIZED":
            raise UnauthorizedError
        if result.text == "NOT_FOUND":
            raise NotFoundError

        try:
            data = result.json()
            if 'error' in data:
                error = data['error']
                if error['code'] == "UNAUTHORIZED":
                    raise UnauthorizedError
                if error['code'] == "INVALID_PASSWORD":
                    raise InvalidPasswordError
                if error['code'] == "INVALID_OLD_PASSWORD":
                    raise InvalidOldPasswordError
                if error['code'] == "SOME_PASSWORD":
                    raise SomePasswordError
                if error['code'] == "SESSION_REVOKED":
                    raise TokenRevokedError(self.refresh_token)
                if error['code'] == "SESSION_NOT_FOUND":
                    raise TokenNotFoundError(self.refresh_token)
                if error['code'] == "REFRESH_TOKEN_MISSING":
                    raise MissingTokenError
                if error['code'] == 'NOT_FOUND':
                    raise NotFoundError
                else:
                    raise ITDError(code=data['error']['code'], message=data["code"]["message"])
        except JSONDecodeError:
            pass

        return result

    async def get(self, url: str, params: dict | None = None) -> httpx.Response:
        return await self._unauthorized_wrapper(self.session.get, url, params=params)

    async def post(self, url: str, json: Any | None = None, params: dict | None = None,
                   cookies: dict | None = None, files: dict | None = None) -> httpx.Response:
        return await self._unauthorized_wrapper(self.session.post, url, json=json, params=params, cookies=cookies, files=files)

    async def delete(self, url: str, json: Any | None = None, params: dict | None = None) -> httpx.Response:
        return await self._unauthorized_wrapper(self.session.post, url, json=json, params=params)

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
            raise InvalidPasswordError

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
            MissingTokenError: Токен не указан (равен пустой строке)
        """
        if len(self.refresh_token) == 0:
            raise MissingTokenError

        result = await self._request(
            self.session.post,
            "api/v1/auth/refresh",
            cookies={"refresh_token": self.refresh_token}
        )
        self.access_token = result.json()["accessToken"]
        return self.access_token

    async def upload_file(self, file: IO[bytes]) -> File:
        """Загрузить файл.

        Args:
            file: файл

        Raises:
            UnauthorizedError: неверный access токен
        """
        result = await self.post("api/files/upload", files={'file': file})
        return File.from_json(result.json())

    async def get_file(self, file_id: UUID | str) -> File:
        """Получить файл.

        Args:
            file_id: UUID файла

        Raises:
            UnauthorizedError: неверный access токен
        """
        if isinstance(file_id, str):
            file_id = UUID(file_id)
        result = await self.get(f"api/files/{file_id}")
        return File.from_json(result.json())


    async def delete_file(self, file_id: UUID | str):
        """Удалить файл

        Args:
            file_id: UUID файла

        Raises:
            UnauthorizedError: неверный access токен
            FileNotFoundError: Файл не найден, или нет прав доступа к нему
        """
        if isinstance(file_id, str):
            file_id = UUID(file_id)
        try:
            await self.delete(f"api/files/{file_id}")
        except NotFoundError:
            raise FileNotFoundError


    async def get_trending_hashtags(self, limit: int = 10) -> list[HashTag]:
        """Получить популярные хештеги.

        Args:
            limit: максимальное количество выданных хештегов

        Raises:
            UnauthorizedError: неверный access токен
        """
        validate_limit(limit)
        result = await self.get("api/hashtags/trending", params={"limit": limit})
        data = result.json()["data"]
        hashtags = []
        for hashtag in data["hashtags"]:
            hashtags.append(HashTag.from_json(hashtag))

        return hashtags

    async def search_hashtags(self, query: str, limit: int = 20) -> list[
        HashTag]:
        """Найти хештеги.

        Args:
            query: текст запроса
            limit: максимальное количество выданных хештегов

        Raises:
            UnauthorizedError: неверный access токен
        """
        validate_limit(limit)
        result = await self.get(f"api/hashtags", params={"q": query, "limit": limit})
        data = result.json()["data"]

        hashtags = []
        for hashtag in data["hashtags"]:
            hashtags.append(HashTag.from_json(hashtag))

        return hashtags

    async def get_posts_by_hashtag(
            self, hashtag_name: str, cursor: UUID | str | None = None,
            limit: int = 20
    ) -> tuple[HashTag, HashtagsPagination, list]:
        """Посты по хештегу.

        Args:
            hashtag_name: текст хештега
            cursor: UUID последнего поста на прошлой странице
            limit: максимальное количество выданных постов

        Raises:
            UnauthorizedError: неверный access токен
            NotFoundError: Хештег не найден

        """
        validate_limit(limit)
        if isinstance(cursor, str):
            cursor = UUID(cursor)

        try:
            result = await self.get(
                f"api/hashtags/{hashtag_name}/posts",
                params={"limit": limit} | ({} if cursor is None else {"cursor": cursor})

            )
        except NotFoundError:
            raise NotFoundError("NOT_FOUND",f"Хештег {hashtag_name} не найден")

        data = result.json()["data"]
        hashtag = data["hashtag"]
        if hashtag is None:
            raise NotFoundError("NOT_FOUND", f"Хештег {hashtag_name} не найден")
        hashtag = HashTag.from_json(hashtag)

        pagination = HashtagsPagination.from_json(data["pagination"])

        # TODO преобразование в Post когда его напишу
        posts = data["posts"]

        return hashtag, pagination, posts