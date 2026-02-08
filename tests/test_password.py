from aioitd import AsyncITDClient, InvalidPasswordError, SomePasswordError, InvalidOldPasswordError
import unittest

from tests.setting import refresh_token, password

class TestPassword(unittest.IsolatedAsyncioTestCase):
    async def test_invalid(self):
        try:
            async with AsyncITDClient(refresh_token) as client:
                await client.change_password(password, "1")
        except InvalidPasswordError:
            pass
        else:
            self.fail("InvalidPasswordError не выброшено")

    async def test_some(self):
        try:
            async with AsyncITDClient(refresh_token) as client:
                await client.change_password(password, password)
        except SomePasswordError:
            pass
        else:
            self.fail("SomePasswordError не выброшено")

    async def test_invalid_old(self):
        try:
            async with AsyncITDClient(refresh_token) as client:
                await client.change_password("123", password)
        except InvalidOldPasswordError:
            pass
        else:
            self.fail("InvalidOldPasswordError не выброшено")

    async def test_change(self):
        async with AsyncITDClient(refresh_token) as client:
            await client.change_password(password, "123456789F")
