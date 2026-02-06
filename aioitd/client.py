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





