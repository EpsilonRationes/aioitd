from uuid import uuid8

import pytest

from tests.api import client, access_token

from aioitd import UnauthorizedError, ParamsValidationError, ITDError
from aioitd.api.notifications import get_notifications, get_notifications_count, read_all_notifications, \
    read_notification, read_batch_notifications, get_notification_settings, update_notification_settings


@pytest.mark.asyncio
async def test_get_notifications(client, access_token):
    with pytest.raises(UnauthorizedError):
        await get_notifications(client, "123")

    has_more, notification = await get_notifications(client, access_token)

    has_more, notification = await get_notifications(client, access_token, limit=0)
    has_more, notification = await get_notifications(client, access_token, limit=10000)

    has_more, notification = await get_notifications(client, access_token, limit=-1)

    with pytest.raises(ITDError):
        has_more, notification = await get_notifications(client, access_token, offset=-10)

    has_more, notification = await get_notifications(client, access_token, offset=0)

    has_more, notification = await get_notifications(client, access_token, offset=100000)


@pytest.mark.asyncio
async def test_read_notification(client, access_token):
    with pytest.raises(UnauthorizedError):
        await read_notification(client, '123', uuid8())

    await read_notification(client, access_token, uuid8())


@pytest.mark.asyncio
async def test_read_notification(client, access_token):
    with pytest.raises(UnauthorizedError):
        await read_batch_notifications(client, '123', [])

    await read_batch_notifications(client, access_token, [])
    await read_batch_notifications(client, access_token, [uuid8(), uuid8()])
    await read_batch_notifications(client, access_token, [uuid8()] * 20)

    with pytest.raises(ParamsValidationError):
        await read_batch_notifications(client, access_token, [uuid8()] * 21)


@pytest.mark.asyncio
async def test_get_notifications_count(client, access_token):
    with pytest.raises(UnauthorizedError):
        await get_notifications_count(client, '123')

    await get_notifications_count(client, access_token)


@pytest.mark.asyncio
async def test_read_all_notifications(client, access_token):
    with pytest.raises(UnauthorizedError):
        await read_all_notifications(client, '123')

    await read_all_notifications(client, access_token)


@pytest.mark.asyncio
async def test_get_notifications_settings(client, access_token):
    with pytest.raises(UnauthorizedError):
        await get_notification_settings(client, '123')
    await get_notification_settings(client, access_token)


@pytest.mark.asyncio
async def test_update_notifications_settings(client, access_token):
    with pytest.raises(UnauthorizedError):
        await update_notification_settings(client, '123')
    await update_notification_settings(client, access_token)
    await update_notification_settings(client, access_token, enabled=False)
    await update_notification_settings(client, access_token, True, True, True, True, True, True, True)