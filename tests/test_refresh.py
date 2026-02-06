from aioitd import ITDClient, TokenNotFoundError, TokenRevokedError
import unittest


refresh_token_success = "9ebaa32b2ecf095a24e5fc8c136ca17353ed065a92318c0968a03013ca7e85e3"
refresh_token_revoked = "623f6990eb038550263e304d3c6cf2817687b1289a52f87738351d6cc781a753"

class TestRefresh(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    async def wrapper(refresh_token: str) -> str:
        async with ITDClient(refresh_token) as client:
            return await client.refresh()

    async def test_success(self):
        self.assertTrue(isinstance(await self.wrapper(refresh_token_success), str))

    async def test_not_found(self):
        try:
            await self.wrapper("Not_a_token")
            self.fail("Ошибки нет")
        except TokenNotFoundError:
            pass
        else:
            self.fail("Не та ошибка")


    async def test_revoked(self):
        try:
            await self.wrapper(refresh_token_revoked)
            self.fail("Ошибки нет")
        except TokenRevokedError:
            pass
        else:
            self.fail("Не та ошибка")

    async def test_token_len(self):
        try:
            await self.wrapper("")
            self.fail("Ошибки нет")
        except ValueError:
            pass
        else:
            self.fail("Не та ошибка")
