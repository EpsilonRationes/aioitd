import pytest

from aioitd import AlreadyDeletedError, AccountDeletedError, NotFoundError, NotDeletedError
from aioitd.fetch import decode_jwt_payload
from tests.api import client, refresh_token, access_token
from aioitd.api import refresh, delete_account, get_posts, search_hashtags, get_me, get_posts_by_user, \
    get_follow_status, restore_account


@pytest.mark.asyncio
async def test_delete_account(client):
    refresh_token2 = ''
    access_token = await refresh(client, refresh_token2)
    access_token2 = await refresh(client, refresh_token)
    await delete_account(client, access_token)

    with pytest.raises(AlreadyDeletedError):
        await delete_account(client, access_token)

    with pytest.raises(AccountDeletedError):
        await get_posts(client, access_token)

    await search_hashtags(client, '123')

    await get_me(client, access_token)

    user_id = decode_jwt_payload(access_token)['sub']
    with pytest.raises(NotFoundError):
        await get_posts_by_user(client, access_token2, user_id)
    print(await get_follow_status(client, access_token2, [user_id]))

    await restore_account(client, access_token)


@pytest.mark.asyncio
async def test_restore_account(client, access_token):
    with pytest.raises(NotDeletedError):
        await restore_account(client, access_token)