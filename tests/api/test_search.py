import pytest

from tests.api import client
from aioitd import ParamsValidationError
from aioitd.api.search import search


@pytest.mark.asyncio
async def test_search(client):
    await search(client, "a")
    await search(client, "a" * 1001)

    with pytest.raises(ParamsValidationError):
        await search(client, "a", user_limit=0)

    await search(client, "a", user_limit=1)
    await search(client, "a", user_limit=20)

    with pytest.raises(ParamsValidationError):
        await search(client, "a", user_limit=21)
