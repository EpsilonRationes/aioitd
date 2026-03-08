from typing import NamedTuple
from uuid import UUID

import httpx

from aioitd.fetch import get, add_bearer, post, delete, put
from aioitd.models.users import BlockedAuthor, FullUser, UserBlockedByMe, Me, PinWithDate, UserBlockMe, PrivateUser, \
    FullMe, \
    UserWithFollowing, Clan, Privacy, Profile, Visibility, UserWithFollowersCount, PinSlug
from aioitd.models.base import PagePagination


async def get_user(
        client: httpx.AsyncClient,
        access_token: str,
        username_or_id: str | UUID,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> FullUser | UserBlockedByMe | UserBlockMe | PrivateUser:
    """Получить данные пользователя.

    Args:
        client: httpx.AsyncClient
        access_token: access токен
        username_or_id: имя пользователя или его UUID
        domain: домен

    Raises:
        UnauthorizedError: необходима авторизация
        NotFoundError: пользователь не найден
        UserBlockedError: пользователь заблокирован
    """
    response = await get(
        client,
        f"https://{domain}/api/users/{username_or_id}",
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()
    if 'isBlockedByMe' in data:
        return UserBlockedByMe(**data)
    elif 'isBlockedByThem' in data:
        return UserBlockMe(**data)
    elif 'isPrivate' in data:
        return PrivateUser(**data)
    else:
        return FullUser(**data)


async def get_me(client: httpx.AsyncClient, access_token: str, domain: str = "xn--d1ah4a.com", **kwargs) -> FullMe:
    """Получить текущего пользователя.

    Args:
        client: httpx.AsyncClient
        access_token: access токен
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
    """
    response = await get(
        client,
        f"https://{domain}/api/users/me",
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()
    data['isFollowedBy'] = False
    data['isFollowing'] = False
    return FullMe(**data)


async def follow(
        client: httpx.AsyncClient,
        access_token: str,
        username_or_id: str | UUID,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> int:
    """Подписаться на пользователя

    Args:
        client: httpx.AsyncClient
        access_token: access токен
        username_or_id: имя пользователя или его UUID
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: Пользователь не найден
        ConflictError: Вы уже подписана на этого пользователя
        ValidationError: Нельзя подписаться на себя
        UserBlockedError: пользователь заблокирован

    Returns: Количество подписчиков пользователя
    """
    response = await post(
        client,
        f"https://{domain}/api/users/{username_or_id}/follow",
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    return response.json()["followersCount"]


async def unfollow(
        client: httpx.AsyncClient,
        access_token: str,
        username_or_id: str | UUID,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> int:
    """Отписать от пользователя

    Args:
        client: httpx.AsyncClient
        access_token: access токен
        username_or_id: имя пользователя или его UUID
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: Пользователь не найден

    Returns: Количество подписчиков пользователя
    """
    response = await delete(
        client,
        f"https://{domain}/api/users/{username_or_id}/follow",
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    return response.json()["followersCount"]


async def get_followers(
        client: httpx.AsyncClient,
        access_token: str,
        username_or_id: str | UUID,
        page: int = 1,
        limit: int = 30,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> tuple[PagePagination, list[UserWithFollowing]]:
    """Получить подписчиков пользователя.

    Args:
        client: httpx.AsyncClient
        access_token: access токен
        username_or_id: имя пользователя или его UUID
        page: страница
        limit: максимальное количество пользователей на странице
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: Пользователь не найден
        ParamsValidationError: 1 <= limit <= 100
        ParamsValidationError: page >= 1
        UserBlockedError: пользователь заблокирован
    """
    response = await get(
        client,
        f"https://{domain}/api/users/{username_or_id}/followers",
        params={"limit": limit, "page": page},
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()["data"]
    pagination = PagePagination(**data['pagination'])
    users = list(map(UserWithFollowing.model_validate, data["users"]))

    return pagination, users


async def get_following(
        client: httpx.AsyncClient,
        access_token: str,
        username_or_id: str | UUID,
        page: int = 1,
        limit: int = 30,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> tuple[PagePagination, list[UserWithFollowing]]:
    """Получить подписчики пользователя.

    Args:
        client: httpx.AsyncClient
        access_token: access токен
        username_or_id: имя пользователя ли его UUID
        page: страница
        limit: максимальное количество пользователей на странице
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: Пользователь не найден
        ParamsValidationError: 1 <= limit <= 100
        ParamsValidationError: page >= 1
        UserBlockedError: пользователь заблокирован

    """
    response = await get(
        client,
        f"https://{domain}/api/users/{username_or_id}/following",
        params={"limit": limit, "page": page},
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()["data"]
    pagination = PagePagination(**data['pagination'])
    users = list(map(UserWithFollowing.model_validate, data["users"]))

    return pagination, users


async def get_top_clans(
        client: httpx.AsyncClient,
        access_token: str,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> list[Clan]:
    """Получить топ кланов.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        domain: домен
    
    Raises:
        UnauthorizedError: ошибка авторизации
    
    """
    response = await get(
        client,
        f'https://{domain}/api/users/stats/top-clans',
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()
    return list(map(Clan.model_validate, data["clans"]))


async def get_who_to_follow(
        client: httpx.AsyncClient,
        access_token: str,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> list[UserWithFollowersCount]:
    """Получить топ по подпискам.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
    """
    response = await get(
        client,
        f'https://{domain}/api/users/suggestions/who-to-follow',
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()
    return list(map(UserWithFollowersCount.model_validate, data["users"]))


async def search_users(
        client: httpx.AsyncClient,
        access_token: str,
        query: str,
        limit: int = 20,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> list[UserWithFollowersCount]:
    """Поиск пользователей.

    Args:
        client: httpx.AsyncClient
        access_token: access токен
        query: текст запроса
        limit: максимальное количество выданных пользователей
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        ValidationError: 1 <= limit <= 50
    """
    response = await get(
        client,
        f"https://{domain}/api/users/search",
        params={"q": query, "limit": limit},
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()["data"]
    return list(map(UserWithFollowersCount.model_validate, data['users']))


class PinsResponse(NamedTuple):
    active_pin: str | None
    pins: list[PinWithDate]


async def get_pins(
        client: httpx.AsyncClient,
        access_token: str,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> PinsResponse:
    """Получить список пин'ов и текущий пин.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        domain: домен

    Raises:
        UnauthorizedError: неверный access токен

    """
    response = await get(
        client,
        f"https://{domain}/api/users/me/pins",
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()["data"]
    return PinsResponse(data['activePin'], list(map(PinWithDate.model_validate, data["pins"])))


async def set_pin(
        client: httpx.AsyncClient,
        access_token: str,
        pin_slug: PinSlug,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> PinSlug:
    """Изменить пин.

    Args:
        client: httpx.AsyncClient
        access_token: access токен
        pin_slug: slug пина
        domain: домен

    Raises:
        UnauthorizedError: неверный access токен
        PinNotOwnedError: вы не обладаете этим пином или такого пина не существует
        ParamsValidationError: 1 <= len(slug) <= 50

    """
    response = await put(
        client,
        f"https://{domain}/api/users/me/pin",
        json={"slug": pin_slug},
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    return PinSlug(response.json()["pin"])


async def delete_pin(
        client: httpx.AsyncClient,
        access_token: str,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> None:
    """Убрать пин.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        domain: домен

    Raises:
        UnauthorizedError: неверный access токен

    """
    await delete(
        client,
        f"https://{domain}/api/users/me/pin",
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )


async def get_privacy(
        client: httpx.AsyncClient,
        access_token: str,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> Privacy:
    """Получить настройки приватности текущего пользователя.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        domain: домен

    Raises:
        UnauthorizedError: неверный access токен

    """
    response = await get(
        client,
        f"https://{domain}/api/users/me/privacy",
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()
    return Privacy(**data)


async def update_privacy(
        client: httpx.AsyncClient,
        access_token: str,
        is_private: bool | None = None,
        likes_visibility: Visibility | None = None,
        wall_access: Visibility | None = None,
        show_last_seen: bool | None = None,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> Privacy:
    """Изменить настройки приватности текущего пользователя.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        is_private: приватный ли пользователь
        likes_visibility: кто может видеть лайкнутые посты
        wall_access: кто может писать на стене
        show_last_seen: показывать время последнего посещения
        domain: домен

    Raises:
        UnauthorizedError: неверный access токен

    """
    params = {}
    if is_private is not None:
        params["isPrivate"] = is_private
    if likes_visibility is not None:
        params["likesVisibility"] = likes_visibility
    if wall_access is not None:
        params["wallAccess"] = wall_access
    if show_last_seen is not None:
        params["showLastSeen"] = show_last_seen

    response = await put(
        client,
        f"https://{domain}/api/users/me/privacy",
        json=params,
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()
    return Privacy(**data)


async def get_profile(
        client: httpx.AsyncClient,
        access_token: str,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> Profile:
    """Профиль текущего пользователя.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        domain: домен

    Raises:
        UnauthorizedError: неверный access токен

    """
    response = await get(
        client,
        f"https://{domain}/api/profile",
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()
    return Profile(**data)


async def update_profile(
        client: httpx.AsyncClient,
        access_token: str,
        bio: str | None = None,
        display_name: str | None = None,
        username: str | None = None,
        banner_id: UUID | None = None,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> Me:
    """Обновить профиль.

    Args:
        client: httpx.AsyncClient
        access_token: access токен
        bio: о себе
        display_name: имя
        username: имя пользователя
        banner_id: UUID файла нового баннера
        domain: домен

    Raises:
        UnauthorizedError: неверный access токен
        ITDError: Био максимум 160 символов
        ITDError: Имя от 1 до 50 символов
        ITDError: Юзернейм 3-50 символов, только буквы, цифры и _
        ForbiddenError: На баннер можно поставить только свой файл
        ValidationError: Баннер может быть только изображением
        UsernameTakenError: Имя пользователя уже занято
    """
    json = {}
    if bio is not None:
        json["bio"] = bio
    if display_name is not None:
        json["displayName"] = display_name
    if username is not None:
        json["username"] = username
    if banner_id is not None:
        json['bannerId'] = str(banner_id)

    response = await put(
        client,
        f"https://{domain}/api/users/me",
        json=json,
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()
    return Me(**data)


async def block(
        client: httpx.AsyncClient,
        access_token: str,
        username_or_id: str | UUID,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> None:
    """Изменить настройки приватности текущего пользователя.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        username_or_id: имя пользователя или UUID
        domain: домен

    Raises:
        UnauthorizedError: неверный access токен
        NotFoundError: пользователь не найден
        ConflictError: пользователь уже заблокирован
        ValidationError: нельзя заблокировать себя
    """
    await post(
        client,
        f"https://{domain}/api/users/{str(username_or_id)}/block",
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )


async def unblock(
        client: httpx.AsyncClient,
        access_token: str,
        username_or_id: str | UUID,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> None:
    """Разблокировать пользователя.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        username_or_id: имя пользователя или UUID
        domain: домен

    Raises:
        UnauthorizedError: неверный access токен
        NotFoundError: пользователь не найден
        ConflictError: пользователь не заблокирован
    """
    await delete(
        client,
        f"https://{domain}/api/users/{str(username_or_id)}/block",
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )


async def get_blocked(
        client: httpx.AsyncClient,
        access_token: str,
        page: int = 1,
        limit: int = 20,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> tuple[PagePagination, list[BlockedAuthor]]:
    """Получить заблокированных пользователей.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        page: страница
        limit: максимальное количество пользователей на странице
        domain: домен

    Raises:
        UnauthorizedError: неверный access токен
        ParamsValidationError: 1 <= limit <= 100
        ParamsValidationError: page >= 1
    """
    response = await get(
        client,
        f"https://{domain}/api/users/me/blocked",
        params={"page": page, "limit": limit},
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()['data']
    pagination = PagePagination(**data["pagination"])
    users = list(map(BlockedAuthor.model_validate, data["users"]))
    return pagination, users


async def get_follow_status(
        client: httpx.AsyncClient,
        access_token: str,
        user_ids: list[UUID],
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> dict[UUID, bool]:
    """Подписаны ли вы на пользователей.

    Args:
        client: httpx.AsyncClient
        access_token: access токен
        user_ids: список UUID пользователей
        domain: домен

    Raises:
        UnauthorizedError: неверный access токен
        ParamsValidationError: len(user_ids) <= 20
    """
    response = await post(
        client,
        f"https://{domain}/api/users/follow-status",
        json={"userIds": list(map(str, user_ids))},
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()['data']
    result = {}
    for key, value in data.items():
        result[UUID(key)] = value
    return result


__all__ = [get_user, get_me, follow, unfollow, get_followers, get_following, get_top_clans, get_who_to_follow,
           search_users, PinsResponse, get_pins, set_pin, delete_pin, get_privacy, update_privacy, get_profile,
           update_profile, block, unblock, get_blocked, get_follow_status]
