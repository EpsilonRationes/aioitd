from aioitd import AsyncITDClient, TokenRevokedError, TokenMissingError, TokenNotFoundError
import unittest


from setting import refresh_token_revoked

class TestRefresh(unittest.IsolatedAsyncioTestCase):
    async def test_revoked(self):
        try:
            async with AsyncITDClient(refresh_token_revoked):
                pass
        except TokenRevokedError:
            pass
        else:
            self.fail("TokenRevokedError не выброшено")

    async def test_missing_token(self):
        try:
            async with AsyncITDClient(""):
                pass
        except TokenMissingError:
            pass
        else:
            self.fail("TokenMissingError не выброшено")

    async def test_token_not_found(self):
        try:
            async with AsyncITDClient("NotAToken"):
                pass
        except TokenNotFoundError:
            pass
        else:
            self.fail("TokenNotFoundError не выброшено")