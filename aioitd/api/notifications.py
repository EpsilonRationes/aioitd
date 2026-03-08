from typing import NamedTuple
from uuid import UUID

import httpx

from aioitd.fetch import add_bearer, get, post
from aioitd.models.notifications import Notification


class NotificationsResponse(NamedTuple):
    has_more: bool
    notifications: list[Notification]


async def get_notifications(
        client: httpx.AsyncClient,
        access_token: str,
        offset: int = 0,
        limit: int = 30,
        domain: str = "xn--d1ah4a.com"
) -> NotificationsResponse:
    """Получить уведомления.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        offset: сдвиг
        limit: максимально количество уведомлений в ответе, любое число
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        ITDError: offset >= 0
    """
    response = await get(
        client,
        f"https://{domain}/api/notifications/",
        params={"limit": limit, "offset": offset},
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()
    return NotificationsResponse(
        data["hasMore"],
        list(map(Notification.model_validate, data["notifications"]))
    )


async def read_batch_notifications(
        client: httpx.AsyncClient,
        access_token: str,
        notifications_ids: list[UUID],
        domain: str = "xn--d1ah4a.com"
) -> int:
    """Пометить прочитанными несколько уведомлений.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        notifications_ids: список UUID уведомлений
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        ParamsValidationError: len(notifications_ids) <= 20

    Returns: Количество прочитанных уведомлений
    """
    response = await post(
        client,
        f"https://{domain}/api/notifications/read-batch",
        json={"ids": list(map(str, notifications_ids))},
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()
    return data["count"]


async def read_notification(
        client: httpx.AsyncClient,
        access_token: str,
        notification_id: UUID,
        domain: str = "xn--d1ah4a.com"
) -> bool:
    """Пометить сообщение прочитанным.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        notification_id: UUID уведомления
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации

    """
    response = await post(
        client,
        f"https://{domain}/api/notifications/{notification_id}/read",
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()
    return data["success"]


async def get_notifications_count(
        client: httpx.AsyncClient,
        access_token: str,
        domain: str = "xn--d1ah4a.com"
) -> int:
    """Получить количество непрочитанных уведомлений.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации

    Returns: Количество непрочитанных уведомлений.
    """
    response = await get(
        client,
        f"https://{domain}/api/notifications/count",
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()
    return data["count"]


async def read_all_notifications(
        client: httpx.AsyncClient,
        access_token: str,
        domain: str = "xn--d1ah4a.com"
) -> bool:
    """Пометить все уведомления прочитанными.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации

    Returns: успешна ли операция
    """
    response = await post(
        client,
        f"https://{domain}/api/notifications/read-all",
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()
    return data["success"]


__all__ = [NotificationsResponse, get_notifications, read_batch_notifications, read_notification,
           read_all_notifications, get_notifications_count]
