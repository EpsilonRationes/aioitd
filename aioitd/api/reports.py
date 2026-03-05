from uuid import UUID
from enum import Enum

import httpx

from aioitd.fetch import add_bearer, post
from aioitd.models.reports import Report


class Reason(str, Enum):
    """Повод жалобы."""
    SPAM = "spam"
    """Спам или нежелательный контент"""

    VIOLENCE = "violence"
    """Спам или нежелательный контент"""

    HATE = "hate"
    """Ненависть или травля"""

    ADULT = "adult"
    """Контент для взрослых (18+)"""

    FRAUD = "misinfo"
    """Дезинформация или обман"""

    OTHER = "other"
    """Другое"""

    def __str__(self):
        return self.value


class ReportTargetType(str, Enum):
    """Тип объекта жалобы"""
    POST = 'post'
    """Пост"""

    COMMENT = 'comment'
    """Комментарий"""

    USER = 'user'
    """Пользователь"""


async def report(
        client: httpx.AsyncClient,
        access_token: str,
        target_id: UUID,
        target_type: ReportTargetType = ReportTargetType.USER,
        reason: Reason = Reason.OTHER,
        description: str = "",
        domain: str = "xn--d1ah4a.com"
) -> Report:
    """Пожаловаться
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        target_id: UUID цели
        target_type: тип цели
        reason: причина
        description: текст репорта
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        RateLimitError: ограничение количества жалоб за время
        ValidationError: не найден пост, пользователь или комментарий по target_id
        ValidationError: нельзя отправить жалобу на один и тот же контент
        PramsValidationError: len(description) <= 1000
    """
    response = await post(
        client,
        f"https://{domain}/api/reports",
        json={"targetId": str(target_id), "targetType": target_type, "reason": reason, "description": description},
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()['data']
    return Report(**data)
