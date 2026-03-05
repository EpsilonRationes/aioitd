import pytest
from httpx import AsyncClient
from aioitd.api.auth import refresh

refresh_token = ""


@pytest.fixture
async def client():
    async with AsyncClient() as client:
        yield client


@pytest.fixture
async def access_token(client):
    yield await refresh(client, refresh_token)
