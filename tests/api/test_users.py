import asyncio

import pytest
from uuid import uuid8, UUID

from aioitd import UnauthorizedError, NotFoundError, ValidationError, ParamsValidationError, ITDError, ForbiddenError, \
    UserBlockedError, ConflictError, PinNotOwnedError, UsernameTakenError, UsernameTakenError
from aioitd.models.users import PinSlug
from tests.api import client, access_token

from aioitd.models.users import FullUser, UserBlockedByMe, PrivateUser, UserBlockMe, Visibility
from aioitd.api.users import get_user, block, unblock, unfollow, follow, get_me, get_followers, get_following, \
    get_top_clans, get_who_to_follow, search_users, get_pins, set_pin, delete_pin, get_privacy, update_privacy, \
    get_profile, get_blocked, update_profile, get_follow_status

blocked_user = "zzzuuuk"
private_username = 'infection'

post_id = UUID("f9e1d062-ef17-484b-b02e-11fd0b9cac94")
file_id = UUID("f4399b89-49a1-4068-a0f2-0d8dfd22a81e")
image_id = UUID("a3c4a9fb-4870-49db-b7f1-5358fa0bc27f")
audio_id = UUID("ce120fab-93b8-4ab4-b0b4-543b989e8a1d")
video_id = UUID("9ba2e97f-f986-4a06-9576-81d3961ba342")
not_me_image = UUID("45f8cb85-f1c9-4aa7-a69d-449351e7b4a5")


@pytest.mark.asyncio
async def test_get_user(client, access_token):
    with pytest.raises(UnauthorizedError):
        await get_user(client, "123", 'nowkie')

    nowkie = await get_user(client, access_token, "nowkie")
    await get_user(client, access_token, nowkie.id)

    assert isinstance(nowkie, FullUser)

    with pytest.raises(UserBlockedError):
        await get_user(client, access_token, blocked_user)

    with pytest.raises(NotFoundError):
        await get_user(client, access_token, "!")

    with pytest.raises(NotFoundError):
        await get_user(client, access_token, uuid8())

    # todo user without username

    try:
        await block(client, access_token, 'nowkie')
    except ConflictError:
        pass

    nowkie = await get_user(client, access_token, 'nowkie')

    assert isinstance(nowkie, UserBlockedByMe)

    await unblock(client, access_token, 'nowkie')

    await unfollow(client, access_token, private_username)

    user = await get_user(client, access_token, private_username)
    assert isinstance(user, PrivateUser)

    await follow(client, access_token, private_username)

    user = await get_user(client, access_token, private_username)
    assert isinstance(user, FullUser)

    user = await get_user(client, access_token, 'blue_cir')

    assert isinstance(user, UserBlockMe)


@pytest.mark.asyncio
async def test_get_me(client, access_token):
    with pytest.raises(UnauthorizedError):
        await get_me(client, '123')

    await get_me(client, access_token)


@pytest.mark.asyncio
async def test_follow_unfollow(client, access_token):
    with pytest.raises(UnauthorizedError):
        await follow(client, '123', 'nowkie')

    with pytest.raises(UnauthorizedError):
        await unfollow(client, '123', 'nowkie')

    await follow(client, access_token, 'nowkie')

    with pytest.raises(ConflictError):
        await follow(client, access_token, 'nowkie')

    await unfollow(client, access_token, 'nowkie')
    await unfollow(client, access_token, 'nowkie')

    with pytest.raises(NotFoundError):
        await follow(client, access_token, '!')

    await asyncio.sleep(60)

    with pytest.raises(NotFoundError):
        await unfollow(client, access_token, '!')

    await follow(client, access_token, UUID("5ee59a22-ae5a-49f9-9090-5a72e6285fad"))
    await unfollow(client, access_token, UUID("5ee59a22-ae5a-49f9-9090-5a72e6285fad"))

    me = await get_me(client, access_token)
    with pytest.raises(ValidationError):
        await follow(client, access_token, me.id)
    await unfollow(client, access_token, me.id)

    await unfollow(client, access_token, blocked_user)
    with pytest.raises(UserBlockedError):
        await follow(client, access_token, blocked_user)


@pytest.mark.asyncio
async def test_get_followers(client, access_token):
    with pytest.raises(UnauthorizedError):
        await get_followers(client, '123', 'nowkie')

    with pytest.raises(NotFoundError):
        await get_followers(client, access_token, '!')

    with pytest.raises(ParamsValidationError):
        await get_followers(client, access_token, 'nowkie', limit=0)

    await get_followers(client, access_token, 'nowkie', limit=1)
    await get_followers(client, access_token, 'nowkie', limit=100)

    with pytest.raises(ParamsValidationError):
        await get_followers(client, access_token, 'nowkie', limit=101)

    await get_followers(client, access_token, UUID("5ee59a22-ae5a-49f9-9090-5a72e6285fad"))

    with pytest.raises(UserBlockedError):
        await get_followers(client, access_token, blocked_user)

    p, users1 = await get_followers(client, access_token, 'nowkie', page=1)
    p, users2 = await get_followers(client, access_token, 'nowkie', page=2)

    assert users1[0] == users2[0]

    with pytest.raises(ParamsValidationError):
        await get_followers(client, access_token, 'nowkie', page=0)


@pytest.mark.asyncio
async def test_get_following(client, access_token):
    with pytest.raises(UnauthorizedError):
        await get_following(client, '123', 'nowkie')

    with pytest.raises(NotFoundError):
        await get_following(client, access_token, '!')

    with pytest.raises(ParamsValidationError):
        await get_following(client, access_token, 'nowkie', limit=0)

    await get_following(client, access_token, 'nowkie', limit=1)
    await get_following(client, access_token, 'nowkie', limit=100)

    with pytest.raises(ParamsValidationError):
        await get_following(client, access_token, 'nowkie', limit=101)

    await get_following(client, access_token, UUID("5ee59a22-ae5a-49f9-9090-5a72e6285fad"))

    with pytest.raises(UserBlockedError):
        await get_following(client, access_token, blocked_user)

    with pytest.raises(ParamsValidationError):
        await get_following(client, access_token, 'nowkie', page=0)

    p, users1 = await get_following(client, access_token, 'nowkie', page=1)
    p, users2 = await get_following(client, access_token, 'nowkie', page=2)

    assert users1[0] == users2[0]


@pytest.mark.asyncio
async def test_get_top_clans(client, access_token):
    with pytest.raises(UnauthorizedError):
        await get_top_clans(client, '123')

    await get_top_clans(client, access_token)


@pytest.mark.asyncio
async def test_get_who_to_follow(client, access_token):
    with pytest.raises(UnauthorizedError):
        await get_who_to_follow(client, '123')

    await get_who_to_follow(client, access_token)


@pytest.mark.asyncio
async def test_search_users(client, access_token):
    with pytest.raises(UnauthorizedError):
        await search_users(client, '123', 'q')

    await search_users(client, access_token, '')
    await search_users(client, access_token, '1')
    await search_users(client, access_token, 'g' * 10_001)

    with pytest.raises(ParamsValidationError):
        await search_users(client, access_token, '1', limit=0)

    await search_users(client, access_token, '1', limit=1)
    await search_users(client, access_token, '1', limit=50)

    with pytest.raises(ParamsValidationError):
        await search_users(client, access_token, '1', limit=51)


@pytest.mark.asyncio
async def test_get_pins(client, access_token):
    with pytest.raises(UnauthorizedError):
        await get_pins(client, '123')

    curr_pin, pinns = await get_pins(client, access_token)


@pytest.mark.asyncio
async def test_set_pin(client, access_token):
    with pytest.raises(UnauthorizedError):
        await set_pin(client, '123', '123')

    await set_pin(client, access_token, PinSlug.KIRILL67_202602_INFECTED)

    with pytest.raises(ParamsValidationError):
        await set_pin(client, access_token, "")

    with pytest.raises(PinNotOwnedError):
        await set_pin(client, access_token, "123")

    with pytest.raises(PinNotOwnedError):
        await set_pin(client, access_token, "1" * 50)

    with pytest.raises(ParamsValidationError):
        await set_pin(client, access_token, "1" * 51)


@pytest.mark.asyncio
async def test_delete_pin(client, access_token):
    with pytest.raises(UnauthorizedError):
        await delete_pin(client, '123')

    await delete_pin(client, access_token)
    await delete_pin(client, access_token)


@pytest.mark.asyncio
async def test_get_privacy(client, access_token):
    with pytest.raises(UnauthorizedError):
        await get_privacy(client, '123')

    await get_privacy(client, access_token)


@pytest.mark.asyncio
async def test_update_privacy(client, access_token):
    with pytest.raises(UnauthorizedError):
        await update_privacy(client, '123')

    await update_privacy(client, access_token)

    await update_privacy(client, access_token, show_last_seen=True, likes_visibility=Visibility.EVERYONE)
    await update_privacy(client, access_token, is_private=False, wall_access=Visibility.EVERYONE)


@pytest.mark.asyncio
async def test_get_profile(client, access_token):
    #with pytest.raises(UnauthorizedError):
    await get_profile(client, '123')

    await get_profile(client, access_token)


@pytest.mark.asyncio
async def test_update_profile(client, access_token):
    with pytest.raises(UnauthorizedError):
        await update_profile(client, '123')

    await update_profile(client, access_token)

    await update_profile(client, access_token, bio="")
    try:
        await update_profile(client, access_token, bio="1" * 1001)
    except ITDError as e:
        assert e.message == "Био: максимум 160 символов"

    await update_profile(client, access_token, display_name='123')

    try:
        await update_profile(client, access_token, display_name='1' * 101)
    except ITDError as e:
        assert e.message == "Имя: от 1 до 50 символов"

    try:
        await update_profile(client, access_token, username='1')
    except ITDError as e:
        assert e.message == "Юзернейм: 3-50 символов, только буквы, цифры и _"

    with pytest.raises(ForbiddenError):
        await update_profile(client, access_token, banner_id=not_me_image)

    with pytest.raises(ValidationError):
        await update_profile(client, access_token, banner_id=audio_id)

    with pytest.raises(ValidationError):
        await update_profile(client, access_token, banner_id=video_id)

    with pytest.raises(NotFoundError):
        await update_profile(client, access_token, banner_id=uuid8())

    with pytest.raises(UsernameTakenError):
        await update_profile(client, access_token, username='nowkie')


@pytest.mark.asyncio
async def test_block_unblock(client, access_token):
    with pytest.raises(UnauthorizedError):
        await block(client, '123', 'nowkie')

    await block(client, access_token, 'nowkie')

    with pytest.raises(ConflictError):
        await block(client, access_token, 'nowkie')

    with pytest.raises(NotFoundError):
        await block(client, access_token, '')

    me = await get_me(client, access_token)

    with pytest.raises(ValidationError):
        await block(client, access_token, me.id)

    await unblock(client, access_token, UUID("5ee59a22-ae5a-49f9-9090-5a72e6285fad"))

    with pytest.raises(ConflictError):
        await unblock(client, access_token, UUID("5ee59a22-ae5a-49f9-9090-5a72e6285fad"))


@pytest.mark.asyncio
async def test_get_blocked(client, access_token):
    with pytest.raises(UnauthorizedError):
        await get_blocked(client, '123')

    try:
        await block(client, access_token, "ado")
    except ConflictError:
        pass

    await get_blocked(client, access_token)

    with pytest.raises(ParamsValidationError):
        await get_blocked(client, access_token, limit=0)

    await get_blocked(client, access_token, limit=1)
    await get_blocked(client, access_token, limit=100)

    with pytest.raises(ParamsValidationError):
        await get_blocked(client, access_token, limit=101)

    with pytest.raises(ParamsValidationError):
        await get_blocked(client, access_token, page=0)


@pytest.mark.asyncio
async def test_get_follow_status(client, access_token):
    with pytest.raises(UnauthorizedError):
        await get_follow_status(client, '123', [''])

    await get_follow_status(client, access_token, ["5ee59a22-ae5a-49f9-9090-5a72e6285fad",  uuid8(), uuid8()])

    await get_follow_status(client, access_token, [])

    await get_follow_status(client, access_token, ["5ee59a22-ae5a-49f9-9090-5a72e6285fad"] * 20)
    with pytest.raises(ParamsValidationError):
        await get_follow_status(client, access_token, ["5ee59a22-ae5a-49f9-9090-5a72e6285fad"]*21)