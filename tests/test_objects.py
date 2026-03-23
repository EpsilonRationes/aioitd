from uuid import UUID

import pytest

from tests.api import refresh_token

from aioitd import AsyncITDClient, PostRef, UserRef


@pytest.mark.asyncio
async def test_objects_refs():
    async with AsyncITDClient(refresh_token) as client:
        user = UserRef(UUID("330dea20-bb7c-4c96-ad09-97150f1ad5f6"), client)
        print(await user.get_full())
        user = await client.get_user("330dea20-bb7c-4c96-ad09-97150f1ad5f6")
        print(await user.get_wall_posts())
        post = PostRef("fb68c34d-7b53-456a-9921-b94615aa8026", client)
        print(await post.get_full())


@pytest.mark.asyncio
async def test_client_objects():
    async with AsyncITDClient(refresh_token) as client:
        _, comments = await client.get_post_comments("d96edabe-8486-446e-9709-6f0dfad3a333")
        for comment in comments:
            await comment.like()

        hashtag = client.HashTagRef("8")
        await hashtag.get_posts()


@pytest.mark.asyncio
async def test_options_ref():
    async with AsyncITDClient(refresh_token) as client:
        comm, post = await client.get_post("758f912e-65fa-4db2-9e68-ce33c70460d7")
        post.poll.options[0]._get_id()
