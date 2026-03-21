import re
from functools import wraps
from typing import TypeVar, Callable
from uuid import UUID

T = TypeVar('T', bound=Callable)


def require_client(func: T) -> T:
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if self.client is None:
            raise ValueError(f"{self.__class__.__name__}.{func.__name__} требует AsyncITDClient")
        return await func(self, *args, **kwargs)

    return wrapper


def validate_username(username: str | None) -> str:
    if username is None:
        raise ValueError("username не может быть None")
    if not (3 <= len(username) <= 50):
        raise ValueError(f"Длина юзернейма от 3 до 50, получено {len(username)}: {username!r}")
    if not re.fullmatch(r'[A-Za-z0-9_]+', username):  # + вместо * (хотя бы один символ)
        raise ValueError(
            f"Юзернейм может содержать только латинские буквы, цифры и _, получено: {username!r}"
        )
    return username


def validate_uuid(uuid: str | UUID) -> UUID:
    if isinstance(uuid, UUID):
        return uuid
    try:
        return UUID(uuid)
    except ValueError:
        raise ValueError(f'Неверный формат uuid: "{uuid}"')


def validate_username_or_uuid(username_or_uuid: str | None) -> UUID | str:
    if username_or_uuid is None:
        validate_username(username_or_uuid)
    try:
        return validate_uuid(username_or_uuid)
    except ValueError:
        pass

    return validate_username(username_or_uuid)


def validate_limit(min_val: int, max_val: int, limit: int) -> int:
    if not (min_val <= limit <= max_val):
        raise ValueError(f'Лимит должен быть от {min_val} до {max_val}, передан {limit}')
    return limit


__all__ = ["validate_uuid", "validate_username_or_uuid", "validate_limit", "validate_username", "require_client"]
