import pytest

from tests.api import client, access_token

from aioitd import UnauthorizedError
from aioitd.api.verification import get_verification_status


@pytest.mark.asyncio
async def test_files(client, access_token):
    with pytest.raises(UnauthorizedError):
        await get_verification_status(client, '123')

    await get_verification_status(client, access_token)
