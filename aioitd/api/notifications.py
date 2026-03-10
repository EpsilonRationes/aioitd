from uuid import UUID

import httpx

from aioitd.fetch import add_bearer, get, post, put
from aioitd.models.notifications import Notification, NotificationsSettings


async def get_notifications(
        client: httpx.AsyncClient,
        access_token: str,
        offset: int = 0,
        limit: int = 30,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> tuple[bool, list[Notification]]:
    """Получить уведомления.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        offset: сдвиг
        limit: максимально количество уведомлений в ответе, любое число
        domain: домен

    Returns:
        bool есть ли ещё уведомления, list[Notification] список уведомлений

    Raises:
        UnauthorizedError: ошибка авторизации
        ITDError: offset >= 0
    """
    response = await get(
        client,
        f"https://{domain}/api/notifications/",
        params={"limit": limit, "offset": offset},
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()
    return data["hasMore"], list(map(Notification.model_validate, data["notifications"]))


async def read_batch_notifications(
        client: httpx.AsyncClient,
        access_token: str,
        notifications_ids: list[UUID],
        domain: str = "xn--d1ah4a.com",
        **kwargs
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

    Returns: 
        Количество прочитанных уведомлений
    """
    response = await post(
        client,
        f"https://{domain}/api/notifications/read-batch",
        json={"ids": list(map(str, notifications_ids))},
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()
    return data["count"]


async def read_notification(
        client: httpx.AsyncClient,
        access_token: str,
        notification_id: UUID,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> bool:
    """Пометить сообщение прочитанным.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        notification_id: UUID уведомления
        domain: домен

    Returns:
        Успешна ли операция
    
    Raises:
        UnauthorizedError: ошибка авторизации

    """
    response = await post(
        client,
        f"https://{domain}/api/notifications/{notification_id}/read",
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()
    return data["success"]


async def get_notifications_count(
        client: httpx.AsyncClient,
        access_token: str,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> int:
    """Получить количество непрочитанных уведомлений.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации

    Returns: 
        Количество непрочитанных уведомлений.
    """
    response = await get(
        client,
        f"https://{domain}/api/notifications/count",
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()
    return data["count"]


async def read_all_notifications(
        client: httpx.AsyncClient,
        access_token: str,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> bool:
    """Пометить все уведомления прочитанными.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации

    Returns: 
        Успешна ли операция
    """
    response = await post(
        client,
        f"https://{domain}/api/notifications/read-all",
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()
    return data["success"]


async def get_notification_settings(
        client: httpx.AsyncClient,
        access_token: str,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> NotificationsSettings:
    """Получить настройки уведомлений.

    Args:
        client: httpx.AsyncClient
        access_token: access токен
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации

    Returns: 
        Настройки уведомлений
    """
    response = await get(
        client,
        f"https://{domain}/api/notifications/settings",
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()
    return NotificationsSettings(**data)


async def update_notification_settings(
        client: httpx.AsyncClient,
        access_token: str,
        comments: bool | None = None,
        enabled: bool | None = None,
        follows: bool | None = None,
        mentions: bool | None = None,
        sound: bool | None = None,
        likes: bool | None = None,
        wall_posts: bool | None = None,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> NotificationsSettings:
    """Настроить уведомления

    Args:
        client: httpx.AsyncClient
        access_token: access токен
        comments: комментарии
        enabled: включены ли уведомления
        follows: подписки
        mentions: упоминания
        sound: звуки при уведомлениях
        likes: лайки
        wall_posts: посты на стене
        domain: домен

    Returns:
        Новые настройки уведомлений

    Raises:
        UnauthorizedError: ошибка авторизации
    """
    json = {
        'comments': comments,
        'enabled': enabled,
        'follows': follows,
        'mentions': mentions,
        'sound': sound,
        'likes': likes,
        'wallPosts': wall_posts,
    }
    json = dict(filter(lambda x: x[1] is not None, json.items()))

    response = await put(
        client,
        f"https://{domain}/api/notifications/settings",
        json=json,
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()
    return NotificationsSettings(**data)


__all__ = [
    'get_notifications', 'read_batch_notifications', 'read_notification', 'read_all_notifications',
    'get_notifications_count', 'get_notification_settings', 'update_notification_settings'
]
