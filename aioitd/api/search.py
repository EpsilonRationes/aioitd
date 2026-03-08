from typing import Any

from aioitd.fetch import get
import httpx

from aioitd.models.hashtags import Hashtag
from aioitd.models.users import UserWithFollowersCount


async def search(
        client: httpx.AsyncClient,
        query: str,
        user_limit: int | None = 20,
        hashtag_limit: int | None = 20,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> tuple[list[Hashtag], list[UserWithFollowersCount]]:
    """Поиск

    Args:
        client: httpx.AsyncClient
        query: запрос
        user_limit: максимальное количество выданных пользователей
        hashtag_limit: максимальное количество выданных хештегов
        domain: домен

    Raises:
        ParamsValidationError: 1 <= user_limit <= 20
        ParamsValidationError: 1 <= hashtag_limit <= 20
    """
    params: dict[str, Any] = {'q': query}
    if user_limit is not None:
        params["userLimit"] = user_limit
    if hashtag_limit is not None:
        params["hashtagsLimit"] = hashtag_limit
    response = await get(
        client,
        f"https://{domain}/api/search/",
        params,
        **kwargs
    )
    data = response.json()["data"]
    hashtags = list(map(Hashtag.model_validate, data["hashtags"]))
    users = list(map(UserWithFollowersCount.model_validate, data["users"]))
    return hashtags, users


__all__ = [search]
