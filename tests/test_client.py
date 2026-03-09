import pytest

from tests.api import refresh_token

from aioitd import AsyncITDClient


@pytest.mark.asyncio
async def test_client():
    async with AsyncITDClient() as client:
        hashtags = await client.search_hashtags('q')
        hashtags = await client.get_trending_hashtags()
        hashtag, pagination, posts = await client.get_posts_by_hashtag('8')

    async with AsyncITDClient(refresh_token) as client:
        await client.get_posts()
        has_more, notifications = await client.get_notifications()

        async with client.connect_notifications() as events:
            async for event in events:
                print(event)
                break
