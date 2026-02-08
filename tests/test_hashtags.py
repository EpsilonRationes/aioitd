from aioitd import AsyncITDClient, InvalidPasswordError, SomePasswordError, InvalidOldPasswordError, ValidationError, \
    NotFoundError
import unittest

from tests.setting import refresh_token, password

class TestHashtags(unittest.IsolatedAsyncioTestCase):
    async def test_invalid(self):
        try:
            async with AsyncITDClient(refresh_token) as client:
                await client.change_password(password, "1")
        except InvalidPasswordError:
            pass
        else:
            self.fail("InvalidPasswordError не выброшено")

    async def test_treading(self):
        async with AsyncITDClient(refresh_token) as client:
            result = await client.get_trending_hashtags()

    async def test_treading_limit(self):
        try:
            async with AsyncITDClient(refresh_token) as client:
                await client.get_trending_hashtags(limit=51)
        except ValidationError:
            pass
        else:
            self.fail("ValidationError не выброшено")

    async def test_search_hashtags_limit(self):
        try:
            async with AsyncITDClient(refresh_token) as client:
                await client.search_hashtags("f", limit=51)
        except ValidationError:
            pass
        else:
            self.fail("ValidationError не выброшено")

    async def testh_search(self):
        async with AsyncITDClient(refresh_token) as client:
            await client.search_hashtags("f")

    async def testh_search_query_limit(self):
        try:
            async with AsyncITDClient(refresh_token) as client:
                await client.search_hashtags("f"*101)
        except ValidationError:
            pass
        else:
            self.fail("ValidationError не выброшено")

    async def testh_posts_by_hashtag(self):
        async with AsyncITDClient(refresh_token) as client:
            await client.search_hashtags("8")

    async def testh_post_by_hashtag_limit(self):
        try:
            async with AsyncITDClient(refresh_token) as client:
                await client.get_posts_by_hashtag('8', 51)
        except ValidationError:
            pass
        else:
            self.fail("ValidationError не выброшено")

    async def testh_post_by_hashtag_not_found(self):
        try:
            async with AsyncITDClient(refresh_token) as client:
                await client.get_posts_by_hashtag('!!!')
        except NotFoundError:
            pass
        else:
            self.fail("NotFoundError не выброшено")