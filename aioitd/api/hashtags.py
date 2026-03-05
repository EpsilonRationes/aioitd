from uuid import UUID

import httpx

from aioitd.exceptions import NotFoundError
from aioitd.fetch import get
from aioitd.models.hashtags import Hashtag, HashtagPost
from aioitd.models.base import Pagination


async def search_hashtags(
        client: httpx.AsyncClient,
        query: str,
        limit: int = 20,
        domain: str = "xn--d1ah4a.com"
) -> list[Hashtag]:
    """Поиск хештегов.

    Args:
        client: httpx.AsyncClient
        query: текст запроса
        limit: максимальное количество выданных хештегов
        domain: домен

    Raises:
        ParamsValidationError: 1 <= limit <= 100
        ParamsValidationError: len(query) <= 100
    """
    response = await get(client, f"https://{domain}/api/hashtags", params={"q": query, "limit": limit})
    data = response.json()["data"]
    return list(map(Hashtag.model_validate, data["hashtags"]))


async def get_trending_hashtags(
        client: httpx.AsyncClient,
        limit: int = 10,
        domain: str = "xn--d1ah4a.com"
) -> list[Hashtag]:
    """Получить популярные хештеги.

    Args:
        client: httpx.AsyncClient
        limit: максимальное количество выданных хештегов
        domain: домен

    Raises:
        ParamsValidationError: 1 <= limit <= 50
    """
    response = await get(client, f"https://{domain}/api/hashtags/trending", params={"limit": limit})
    data = response.json()["data"]
    return list(map(Hashtag.model_validate, data["hashtags"]))


async def get_posts_by_hashtag(
        client: httpx.AsyncClient,
        hashtag_name: str,
        cursor: str | None = None,
        limit: int = 20,
        domain: str = "xn--d1ah4a.com"
) -> tuple[Hashtag, Pagination, list[HashtagPost]]:
    """Посты по хештегу.

    Args:
        client: httpx.AsyncClient
        hashtag_name: текст хештега
        cursor: next_cursor предыдущей страницы
        limit: максимальное количество выданных постов
        domain: домен

    Raises:
        NotFoundError: Хештег не найден
        ParamsValidationError: 1 <= limit <= 50
    """
    params = {'limit': limit}
    if cursor is not None:
        params['cursor'] = cursor

    try:
        response = await get(
            client,
            f"https://{domain}/api/hashtags/{hashtag_name}/posts",
            params=params,
        )
    except NotFoundError:
        raise NotFoundError("NOT_FOUND", f"Хештег '{hashtag_name}' не найден")

    data = response.json()["data"]
    hashtag = data["hashtag"]
    if hashtag is None:
        raise NotFoundError("NOT_FOUND", f"Хештег '{hashtag_name}' не найден")
    hashtag = Hashtag(**hashtag)
    pagination = Pagination(**data["pagination"])
    posts = list(map(HashtagPost.model_validate, data["posts"]))
    return hashtag, pagination, posts


