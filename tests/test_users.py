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

    async def test_get_privacy(self):
        async with AsyncITDClient(refresh_token) as itd:
            privacy = await itd.get_privacy()

    async def test_update_privacy(self):
        async with AsyncITDClient(refresh_token) as itd:
            privacy = await itd.update_privacy(likes_visibility="followers")

    async def test_profile(self):
        async with AsyncITDClient(refresh_token) as itd:
            profile = await itd.get_profile()

    async def test_block_unblock(self):
        async with AsyncITDClient(refresh_token) as itd:
            await itd.block("nowkie")
            await itd.unblock("nowkie")

    async def test_get_user_blocked(self):
        async with AsyncITDClient(refresh_token) as itd:
            await itd.block("nowkie")
            user = await itd.get_user("nowkie")

    async def test_get_blocked_users(self):
        async with AsyncITDClient(refresh_token) as itd:
            pagination, users = await itd.get_blocked()

    async def test_get_user_who_blocked_me(self):
        async with AsyncITDClient(refresh_token) as itd:
            user = await itd.get_user("FIRST_TM")
