import pytest
from tests.api import client


from aioitd.api import get_changelog


@pytest.mark.asyncio
async def test_get_changelog(client):
    await get_changelog(client)
