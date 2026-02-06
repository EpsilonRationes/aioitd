from typing import Any

import httpx
from dataclasses import dataclass
from aioitd.api import add_bearer, UnauthorizedError, UnknowError, NotFoundError, Pagination
from uuid import UUID


@dataclass
class HashTag:
    """Хештег.

    Attributes:
        id: UUID хештега
        name: текст хештега
        posts_count: количество хештегов
    """
    id: UUID
    name: str
    posts_count: int

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> HashTag:
        return HashTag(
            id=UUID(data["id"]),
            name=data["name"],
            posts_count=data["postsCount"]
        )


async def get_trending_hashtags(session: httpx.AsyncClient, access_token: str, limit: int = 10) -> list[HashTag]:
    """Получить популярные хештеги.

    Args:
        session: httpx.AsyncClient
        access_token: access токен
        limit: максимальное количество выданных хештегов

    Raises:
        UnauthorizedError: неверный access токен
    """
    if not (1 <= limit <= 50):
        raise ValueError("limit должен быть больше от 1 до 50")
    result = await session.get(
        f"https://xn--d1ah4a.com/api/hashtags/trending?limit={limit}",
        headers={"authorization": add_bearer(access_token)}
    )

    if result.text == "UNAUTHORIZED":
        raise UnauthorizedError

    response = result.json()
    if 'error' in response:
        raise UnknowError(code=response['error']['code'], message=response['error']['message'])

    hashtags = []
    for hashtag in response["data"]["hashtags"]:
        hashtags.append(HashTag(
            id=UUID(hashtag["id"]),
            name=hashtag["name"],
            posts_count=hashtag["postsCount"]
        ))

    return hashtags


async def search_hashtags(session: httpx.AsyncClient, access_token: str, query: str, limit: int = 20) -> list[HashTag]:
    """Найти хештеги.

    Args:
        session: httpx.AsyncClient
        access_token: access токен
        query: текст запроса
        limit: максимальное количество выданных хештегов

    Raises:
        UnauthorizedError: неверный access токен
    """
    if not (1 <= limit <= 50):
        raise ValueError("limit должен быть больше от 1 до 50")
    result = await session.get(
        f"https://xn--d1ah4a.com/api/hashtags?q={query}&limit={limit}",
        headers={"authorization": add_bearer(access_token)}
    )

    response = result.json()
    if 'error' in response:
        raise UnknowError(code=response['error']['code'], message=response['error']['message'])

    if result.text == "UNAUTHORIZED":
        raise UnauthorizedError

    hashtags = []
    for hashtag in response["data"]["hashtags"]:
        hashtags.append(HashTag.from_json(hashtag))

    return hashtags


@dataclass
class HashtagsPagination(Pagination):
    """Пагинация постов при поиске по хештегу

    Attributes:
        next_cursor: UUID последнего поста на странице
    """
    next_cursor: UUID

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> HashtagsPagination:
        pagination = super().from_json(data)
        return HashtagsPagination(
            **pagination.__dict__,
            next_cursor=UUID(data["nextCursor"])
        )


async def get_posts_by_hashtag(
        session: httpx.AsyncClient, access_token: str, hashtag_name: str,  cursor: UUID | str | None = None, limit: int = 20
) -> tuple[HashTag, HashtagsPagination, list]:
    """Посты по хештегу.

    Args:
        session: httpx.AsyncClient
        access_token: access токен
        hashtag_name: текст хештега
        cursor: UUID последнего поста на прошлой странице
        limit: максимальное количество выданных постов

    Raises:
        UnauthorizedError: неверный access токен
        NotFoundError: Хештег не найден

    """
    if not (1 <= limit <= 50):
        raise ValueError("limit должен быть больше от 1 до 50")
    if isinstance(cursor, str):
        cursor = UUID(cursor)

    result = await session.get(
        f"https://xn--d1ah4a.com/api/hashtags/{hashtag_name}/posts?limit={limit}" if cursor is None
        else f"https://xn--d1ah4a.com/api/hashtags/{hashtag_name}/posts?limit={limit}&cursor={cursor}",
        headers={"authorization": add_bearer(access_token)}
    )

    if result.text == "NOT_FOUND":
        raise NotFoundError(f"Хештег {hashtag_name} не найден")

    if result.text == "UNAUTHORIZED":
        raise UnauthorizedError

    response = result.json()
    if 'error' in response:
        raise UnknowError(code=response['error']['code'], message=response['error']['message'])

    hashtag = response["data"]["hashtag"]
    if hashtag is None:
        raise NotFoundError(f"Хештег {hashtag_name} не найден")
    hashtag = HashTag.from_json(hashtag)

    pagination = HashtagsPagination.from_json(response["data"]["pagination"])

    # TODO преобразование в Post когда его напишу
    posts = response["data"]["posts"]

    return hashtag, pagination, posts
