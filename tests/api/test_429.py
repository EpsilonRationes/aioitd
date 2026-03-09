import asyncio

import pytest

from tests.api import client, access_token

from aioitd.api.users import get_me



@pytest.mark.asyncio
async def test_429(client, access_token):
    tasks = []
    for _ in range(100):
        tasks.append(get_me(client, access_token))
    await asyncio.gather(*tasks)


@pytest.mark.asyncio
async def test_429_2(client, access_token):
    tasks = []
    for _ in range(100):
        await get_me(client, access_token)
        await asyncio.sleep(0.2)