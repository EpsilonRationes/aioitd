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


@pytest.mark.asyncio
async def test_get_me_uuid():
    async with AsyncITDClient(refresh_token) as client:
        await client.get_me_uuid()

@pytest.mark.asyncio
async def test_is_token_expired():
    async with AsyncITDClient(refresh_token) as client:
        await client.get_me()
        client._access_token = "eyJhbGciOiJFZERTQSIsImtpZCI6Imw3azBzcUJSYWVmRVE2V2JiWkhPWVNiZV9SWDRIWDh1MkxXWV9qVnJWVHciLCJ0eXAiOiJKV1QifQ.eyJyb2xlcyI6WyJ1c2VyIl0sInNpZCI6IjVhZGNjM2Y0LWRhNjUtNDdkMC1hMDc2LTQyZDc3OWIwNDM5ZSIsImlzQWN0aXZlIjp0cnVlLCJzdWIiOiIzMzBkZWEyMC1iYjdjLTRjOTYtYWQwOS05NzE1MGYxYWQ1ZjYiLCJpYXQiOjE3NzMxMTg0MjcsImlzcyI6ImF1dGgtc2VydmljZSIsImV4cCI6MTc3MzExOTMyNywianRpIjoiZmRjMWU5MmEtYTBhZS00MGNiLThhZmUtMjFkMDJjYmZmY2EwIn0.uXn13PW1DjpYtBfmzNnhLeBLHx2yC3jgVamENcvE0FtU1ReMtSvg4xuvm1L-N5x-dHKYhsSJHBqZLqvLQOCxAQ"
        await client.get_me()
