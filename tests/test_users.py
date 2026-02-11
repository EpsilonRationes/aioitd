from aioitd import AsyncITDClient, InvalidPasswordError, SomePasswordError, InvalidOldPasswordError, ValidationError, \
    NotFoundError
import unittest

from tests.setting import refresh_token, password


class TestUsers(unittest.IsolatedAsyncioTestCase):
    async def test_get_user(self):
        async with AsyncITDClient(refresh_token) as itd:
            user = await itd.get_user("nowkie")

    async def test_update_profile(self):
        async with AsyncITDClient(refresh_token) as itd:
            me = await itd.update_profile(bio="Updated_bio")

    async def test_get_me(self):
        async with AsyncITDClient(refresh_token) as itd:
            me = await itd.get_me()

    async def test_get_followers(self):
        async with AsyncITDClient(refresh_token) as itd:
            pagination, followers = await itd.get_followers("nowkie")

    async def test_get_following(self):
        async with AsyncITDClient(refresh_token) as itd:
            pagination, followers = await itd.get_following("nowkie")

    async def test_get_top_clans(self):
        async with AsyncITDClient(refresh_token) as itd:
            clans = await itd.get_top_clans()

    async def test_get_who_to_follows(self):
        async with AsyncITDClient(refresh_token) as itd:
            clans = await itd.get_who_to_follow()

    async def test_search_users(self):
        async with AsyncITDClient(refresh_token) as itd:
            users = await itd.search_users("n")

    async def test_get_pins(self):
        async with AsyncITDClient(refresh_token) as itd:
            pins = await itd.get_pins()


