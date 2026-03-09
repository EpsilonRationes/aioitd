import pytest

from tests.api import client

from aioitd.api.hashtags import search_hashtags, get_trending_hashtags, get_posts_by_hashtag
from aioitd.exceptions import NotFoundError, ParamsValidationError


@pytest.mark.asyncio
async def test_search_hashtags(client):
    hashtags = await search_hashtags(client, 'a')

    with pytest.raises(ParamsValidationError):
        hashtags = await search_hashtags(client, "a", limit=0)

    hashtags = await search_hashtags(client, "a", limit=1)
    hashtags = await search_hashtags(client, "a", limit=50)

    with pytest.raises(ParamsValidationError):
        hashtags = await search_hashtags(client, "a", limit=51)

    hashtags = await search_hashtags(client, "")

    hashtags = await search_hashtags(client, "0" * 100)

    with pytest.raises(ParamsValidationError):
        hashtags = await search_hashtags(client, "0" * 101)

    hashtags = await search_hashtags(client, "!")


@pytest.mark.asyncio
async def test_get_treading_hashtags(client):
    hashtags = await get_trending_hashtags(client)

    with pytest.raises(ParamsValidationError):
        hashtags = await get_trending_hashtags(client, limit=0)

    hashtags = await get_trending_hashtags(client, limit=1)
    hashtags = await get_trending_hashtags(client, limit=50)

    with pytest.raises(ParamsValidationError):
        hashtags = await get_trending_hashtags(client, limit=51)


@pytest.mark.asyncio
async def test_get_posts_by_hashtag(client):
    hashtag, pagination, posts = await get_posts_by_hashtag(client, "8")

    with pytest.raises(ParamsValidationError):
        hashtag, pagination, posts = await get_posts_by_hashtag(client, "8", limit=0)

    hashtag, pagination, posts = await get_posts_by_hashtag(client, "8", limit=1)
    hashtag, pagination, posts = await get_posts_by_hashtag(client, "8", limit=50)

    with pytest.raises(ParamsValidationError):
        hashtag, pagination, posts = await get_posts_by_hashtag(client, "8", limit=51)

    with pytest.raises(NotFoundError):
        hashtag, pagination, posts = await get_posts_by_hashtag(client, "8" * 100)

    with pytest.raises(NotFoundError):
        hashtag, pagination, posts = await get_posts_by_hashtag(client, "")

    cursor = None
    while True:
        hashtag, pagination, posts = await get_posts_by_hashtag(client, "femboy", cursor=cursor)
        cursor = pagination.next_cursor
        if cursor is None:
            break
