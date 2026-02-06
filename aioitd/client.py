from functools import wraps
from typing import Callable, Awaitable

import httpx

from aioitd.api import refresh, logout, \
    change_password, UnauthorizedError, is_token_expired


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


class UnknowError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message

    def __str__(self) -> str:
        return f"Неизвестная ошибка. code: '{self.code}', message: '{self.message}'"



class ITDClient:
    """
    Attributes:
        refresh_token: refresh token
        refresh_on_unauthorized: для каждого запроса в случае `UnauthorizedError` вызвать `refresh` и сделать
            запрос ещё раз
        check_access_token_expired: проверять ли access токен. Если True перед каждым запросом токен будет проверен и
            в случае истечения времени жизни, будет вызван `refresh`
    """

    def __init__(self, refresh_token: str, refresh_on_unauthorized: bool = True,
                 check_access_token_expired: bool = False) -> None:
        if len(refresh_token) == 0:
            raise ValueError("`refresh_token` не может быть пустой строкой")
        self.refresh_token = refresh_token
        self.check_access_token_expired = check_access_token_expired
        self.refresh_on_unauthorized = refresh_on_unauthorized
        self.session = httpx.AsyncClient()
        self.access_token = ""

    @staticmethod
    async def refresh_on_token_expired(func: Callable[..., Awaitable]) -> Callable[..., Awaitable]:
        @wraps
        async def wrapper(self: ITDClient, *args, **kwargs):
            if self.check_access_token_expired:
                if is_token_expired(self.access_token):
                    await  self.refresh()
            if self.refresh_on_unauthorized:
                try:
                    return await func(*args, *kwargs)
                except UnauthorizedError:
                    await self.refresh()
                    return await func(*args, **kwargs)
            else:
                return await func(*args, **kwargs)

        return wrapper

    async def __aenter__(self) -> ITDClient:
        await self.refresh()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def close(self) -> None:
        await self.session.aclose()

    async def refresh(self) -> str:
        """Обновить `access_token`

        Returns: access токен

        Raises:
            TokenNotFoundError: токена не существует
            TokenRevokedError: токен отозван
        """
        return await refresh(self.session, self.refresh_token)


    async def logout(self) -> None:
        """Выйти из аккаунта, отозвать refresh токен. Работает при любом токене. Просроченном, не существующем тоже."""
        await logout(self.session, self.refresh_token)

    @refresh_on_token_expired
    async def change_password(self, old_password: str, new_password: str) -> None:
        """Поменять пароль. При успешной смене пароля refresh_token отзывается.

        Args:
            old_password: Старый пароль
            new_password: Новый Пароль

        Raises:
            InvalidPasswordError: Неподходящий пароль
            InvalidOldPasswordError: Указан неверный `old_password`
            SomePasswordError: Пароль должен отличаться от текущего
            UnauthorizedError: истёк access_toke
        """
        return await change_password(self.session, self.access_token, old_password, new_password)


