from uuid import UUID

import pytest

from tests.api import client, access_token

from aioitd import ParamsValidationError
from aioitd.api.reports import report, ReportTargetType
from aioitd.api import get_posts


@pytest.mark.asyncio
async def test_report(client, access_token):
    # with pytest.raises(UnauthorizedError):
    #     await report(client, "123", uuid8())
    #
    # with pytest.raises(ValidationError):
    #     await report(client, access_token, UUID("a157abeb-2d39-4064-bc26-c672fe7a4580"), target_type=ReportTargetType.POST)
    #
    # with pytest.raises(ValidationError):
    #     await report(client, access_token, uuid8())
    _, posts = await get_posts(client, access_token)
    await report(
        client, access_token, posts[0].id,
        description="0" * 1000, target_type=ReportTargetType.POST
    )
    with pytest.raises(ParamsValidationError):
        await report(client, access_token, UUID("ab4f7def-f64a-4873-97de-ab0e5238aea4"), description="0" * 1001)
