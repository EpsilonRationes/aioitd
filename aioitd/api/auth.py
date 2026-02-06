import time
import base64
import json
import re
from typing import Any

import httpx

from aioitd.api.base import *


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


async def refresh(session: httpx.AsyncClient, refresh_token: str) -> str:
    """Получить access_token.

    Args:
        session: httpx.AsyncClient
        refresh_token: refresh токен

    Returns: access токен

    Raises:
        TokenNotFoundError: Такого токена не существует
        TokenRevokedError: Токен отозван
        MissingTokenError: Токен не указан (равен пустой строке)
    """
    if len(refresh_token) == 0:
        raise MissingTokenError()

    result = await session.post(f"https://xn--d1ah4a.com/api/v1/auth/refresh", cookies={"refresh_token": refresh_token})
    response = result.json()
    if 'error' in response:
        if response['error']['code'] == "SESSION_REVOKED":
            raise TokenRevokedError(refresh_token)
        if response['error']['code'] == "SESSION_NOT_FOUND":
            raise TokenNotFoundError(refresh_token)
        if response['error']['code'] == "REFRESH_TOKEN_MISSING":
            raise MissingTokenError()
        raise UnknowError(code=response['error']['code'], message=response['error']['message'])
    else:
        return response["accessToken"]


async def logout(session: httpx.AsyncClient, refresh_token: str) -> None:
    """Выйти из аккаунта, отозвать токен. Работает при любом токене. Просроченном, не существующем и пустой строкой тоже."""
    await session.post("https://xn--d1ah4a.com/api/v1/auth/logout", cookies={"refresh_token": refresh_token})


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


async def change_password(
        session: httpx.AsyncClient,
        access_token: str,
        old_password: str,
        new_password: str,
) -> None:
    """Поменять пароль. При успешной смене пароля `refresh_token` отзывается.

    Args:
        session: httpx.AsyncClient
        access_token: access токен
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

    result = await session.post(
        "https://xn--d1ah4a.com/api/v1/auth/change-password",
        json={"oldPassword": old_password, "newPassword": new_password},
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
