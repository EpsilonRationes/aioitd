import pytest
from tests.api import client

from aioitd.api import get_changelog, get_portal


@pytest.mark.asyncio
async def test_get_changelog(client):
    await get_changelog(client)


@pytest.mark.asyncio
async def test_get_changelog(client):
    await get_portal(client)
