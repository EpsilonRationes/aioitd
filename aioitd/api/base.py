from dataclasses import dataclass
from functools import wraps
from json import JSONDecodeError
from typing import Any, Callable, Awaitable
import time
import base64
import json
import re

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
        self.access_token = ""
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

    @staticmethod
    async def refresh_on_token_expired(func: Callable[..., Awaitable]) -> Callable[..., Awaitable]:
        @wraps
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

    @refresh_on_token_expired
    async def _request(self, method, url: str, **kwargs) -> httpx.Response:
        result = await method(
            f"https://{self.domain}/{url}",
            headers={"authorization": add_bearer(self.access_token)},
            **kwargs
        )

        if result.text == "UNAUTHORIZED":
            raise UnauthorizedError

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
                else:
                    raise ITDError(code=data['error']['code'], message=data["code"]["message"])
        except JSONDecodeError:
            pass

        return result

    async def get(self, url: str, params: dict | None = None) -> httpx.Response:
        return await self._request(self.session.get, url, params=params)

    async def post(self, url: str, json: Any | None = None, params: dict | None = None,
                   cookies: dict | None = None) -> httpx.Response:
        return await self._request(self.session.post, url, json=json, params=params, cookies=cookies)

    async def delete(self, url: str, json: Any | None = None, params: dict | None = None) -> httpx.Response:
        return await self._request(self.session.post, url, json=json, params=params)

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

        await self.post(
            "api/v1/auth/change-password",
            {"oldPassword": old_password, "newPassword": new_password}
        )

    async def logout(self) -> None:
        """Выйти из аккаунта, отозвать токен. Работает при любом токене. Просроченном, не существующем и пустой строкой тоже."""
        await self.post(
            "https://xn--d1ah4a.com/api/v1/auth/logout",
            cookies={"refresh_token": self.refresh_token}
        )

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

        result = await self.post(
            "api/v1/auth/refresh",
            cookies={"refresh_token": self.refresh_token}
        )
        self.access_token = result.json()["accessToken"]
        return self.access_token
