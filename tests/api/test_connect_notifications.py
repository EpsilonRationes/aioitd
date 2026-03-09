import pytest

from tests.api import client, access_token

from aioitd import SSEError
from aioitd.api.stream import connect_notifications


@pytest.mark.asyncio
async def test_connect_notifications(client, access_token):
    with pytest.raises(SSEError):
        async with connect_notifications(client, '123') as events:
            async for event in events:
                print(event)

    async with connect_notifications(client, access_token) as events:
        async for event in events:
            break
