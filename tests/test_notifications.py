from aioitd import AsyncITDClient, InvalidPasswordError, SomePasswordError, InvalidOldPasswordError, ValidationError, \
    NotFoundError
import unittest

from tests.setting import refresh_token, password


class TestNotifications(unittest.IsolatedAsyncioTestCase):
    async def test_get_notifications(self):
        async with AsyncITDClient(refresh_token) as itd:
            notifications = await itd.get_notifications()
