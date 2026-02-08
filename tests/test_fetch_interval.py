import asyncio.tasks
import unittest
from tests.setting import refresh_token
from aioitd import AsyncITDClient, Error429


class TestFetchInterval(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_interval(self):
        async with AsyncITDClient(refresh_token) as client:
            async def fetch():
                try:
                    await client.get_me()
                except Error429:
                    return 0
                return 1
            tasks = []
            for _ in range(100):
                tasks.append(asyncio.tasks.create_task(fetch()))
            total = sum(await asyncio.gather(*tasks))
            self.assertEqual(total, 100)