from dataclasses import dataclass
from json import JSONDecodeError
from typing import Any
from uuid import UUID

import httpx

from aioitd.api import verify_password


def add_bearer(token: str):
    """Добавить Bearer к токену, если отсутствует."""
    if 'Bearer' not in token:
        return "Bearer " + token.strip()
    else:
        return token


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


class FetchManager:
    def __init__(self, refresh_token: str, domain: str = "xn--d1ah4a.com"):
        if len(refresh_token) == 0:
            raise ValueError("refresh токен не может быть пустой строкой")
        self.refresh_token = refresh_token
        self.domain = domain
        self.access_token = None

    async def _request(self, method, url: str, json: Any | None = None) -> httpx.Response:

        result = await method(
            f"https://{self.domain}/{url}",
            headers={"authorization": add_bearer(self.access_token)},
            json=json
        )

        if result.text == "UNAUTHORIZED":
            raise UnauthorizedError

        try:
            data = result.json()
            if 'error' in data:
                if data['error']['code'] == "UNAUTHORIZED":
                    raise UnauthorizedError
                else:
                    raise ITDError(code=data['error']['code'], message=data["code"]["message"])
        except JSONDecodeError:
            pass

        return result

    async def get(self, session: httpx.AsyncClient, url: str, json: Any | None = None) -> httpx.Response:
        return await self._request(session.get, url, json)

    async def post(self, session: httpx.AsyncClient, url: str, json: Any | None = None) -> httpx.Response:
        return await self._request(session.post, url, json)

    async def delete(self, session: httpx.AsyncClient, url: str, json: Any | None = None) -> httpx.Response:
        return await self._request(session.post, url, json)

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

        result = await self.post(
            "api/v1/auth/change-password",
            json={"oldPassword": old_password, "newPassword": new_password}
        )
        result = await session.post(
            ,
            ,
            headers={"authorization": add_bearer(access_token)}
        )

        if result.text == "UNAUTHORIZED":
            raise UnauthorizedError

        response = result.json()
        if 'error' in response:
            if response['error']['code'] == "INVALID_PASSWORD":
                raise InvalidPasswordError
            if response['error']['code'] == "INVALID_OLD_PASSWORD":
                raise InvalidOldPasswordError
            if response['error']['code'] == "SOME_PASSWORD":
                raise SomePasswordError
            raise UnknowError(code=response['error']['code'], message=response['error']['message'])
