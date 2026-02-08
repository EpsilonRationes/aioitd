from itertools import takewhile

from aioitd import AsyncITDClient
import unittest
import asyncio
from tests.setting import refresh_token


class TestRateLimit(unittest.IsolatedAsyncioTestCase):
    async def test_rate_limit(self):
        async with AsyncITDClient(refresh_token) as client:
            tasks = []
            for _ in range(100):
                tasks.append(asyncio.create_task(client.get_me()))
            await asyncio.gather(*tasks)

