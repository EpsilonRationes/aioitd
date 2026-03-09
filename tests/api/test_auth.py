import pytest

from tests.api import client, refresh_token

from aioitd import TokenNotFoundError, TokenMissingError, TokenExpiredError, TokenRevokedError
from aioitd.api.auth import refresh

expired_token = "4a44c449c90450c7dd8863cddb41bbfcce8045b4710af658a92cf6cd86ec161c"
revoked_token = "4e4505cc640c668ebcd8cafc70b316329b62c04d84e28fe559ed6813f924d6bd"


@pytest.mark.asyncio
async def test_refresh(client):
    with pytest.raises(TokenNotFoundError):
        await refresh(client, "123")

    with pytest.raises(TokenMissingError):
        await refresh(client, "")

    with pytest.raises(TokenExpiredError):
        await refresh(client, expired_token)

    with pytest.raises(TokenRevokedError):
        await refresh(client, revoked_token)

    access_token = await refresh(client, refresh_token)
