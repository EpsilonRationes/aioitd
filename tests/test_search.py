from aioitd import AsyncITDClient, ValidationError
import unittest

from tests.setting import refresh_token
from tests import assert_async_raises


class TestSearch(unittest.IsolatedAsyncioTestCase):

    async def test_search(self):
        async with AsyncITDClient(refresh_token) as client:
            result = await client.search("gh")

    async def test_search_limit(self):
        async with AsyncITDClient(refresh_token) as client:
            result = await client.search("gh", 20)

    async def test_search_query(self):
        async with AsyncITDClient(refresh_token) as client:
            result = await client.search("g"*50001, 20)

    async def test_search_users2(self):
        async with AsyncITDClient(refresh_token) as client:
            result = await client.search_users2("q", 20)

    async def test_search_hashtags2(self):
        async with AsyncITDClient(refresh_token) as client:
            result = await client.search_hashtags2("q", 20)

    async def test_search_users(self):
        async with AsyncITDClient(refresh_token) as client:
            result = await client.search_users("1")

    @assert_async_raises(ValidationError)
    async def test_search_users_limit(self):
        async with AsyncITDClient(refresh_token) as client:
            result = await client.search_users("1", 51)
