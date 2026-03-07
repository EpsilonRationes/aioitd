import asyncio

import pytest
from uuid import uuid8, UUID

from PIL.ImageChops import offset

from aioitd import UnauthorizedError, NotFoundError, ValidationError, ParamsValidationError, ITDError, ForbiddenError, \
    NotPinedError, UserBlockedError, VideoRequiresVerificationError, WallClosedError
from aioitd.models.base import Link, Monospace, Strike, Underline, Bold, Italic, Spoiler, Mention, HashTagSpan
from tests.api import client, access_token

from aioitd.api.posts import get_post, delete_post, restore_post, create_post, like_post, delete_like_post, pin_post, \
    unpin_post, get_posts_by_user, get_posts_by_user_liked, get_posts_by_user_wall, get_post_comments, update_post, \
    repost

blocked_user = "zzzuuuk"

post_id = UUID("f9e1d062-ef17-484b-b02e-11fd0b9cac94")
file_id = UUID("f4399b89-49a1-4068-a0f2-0d8dfd22a81e")
image_id = UUID("a3c4a9fb-4870-49db-b7f1-5358fa0bc27f")
audio_id = UUID("ce120fab-93b8-4ab4-b0b4-543b989e8a1d")
video_id = UUID("9ba2e97f-f986-4a06-9576-81d3961ba342")
not_me_image = UUID("45f8cb85-f1c9-4aa7-a69d-449351e7b4a5")

comment_id = UUID("01645b06-63c3-48d5-b161-8e1de1c651cf")
not_me_comment_id = UUID("f6200a84-18b6-4da7-a53a-941e555a7841")

text_post_id = UUID("e99d502f-1e6e-4909-8686-790bbaa379aa")
post_with_audio = UUID("b0fc8ad2-32b3-42cb-bd8d-6e92e8a302cf")
post_with_image = UUID("125016a0-8bb5-49d1-a2f9-590b349c5147")
post_with_video = UUID("d96edabe-8486-446e-9709-6f0dfad3a333")
post_reposted = UUID("60c1571c-aeae-4d55-9390-2ba8d8a744fd")
post_with_comments = UUID("50f9d2de-655e-49cf-8939-9f330eeaad06")
post_with_all_type_comments = UUID("d96edabe-8486-446e-9709-6f0dfad3a333")


@pytest.mark.asyncio
async def test_get_post(client, access_token):
    with pytest.raises(UnauthorizedError):
        c = await get_post(client, '123', uuid8())

    with pytest.raises(NotFoundError):
        c = await get_post(client, access_token, uuid8())

    for post_id in [text_post_id, post_with_comments, post_with_all_type_comments, post_with_video, post_with_audio,
                    post_with_image, post_reposted]:
        await get_post(client, access_token, post_id)


@pytest.mark.asyncio
async def test_delete_restore_post(client, access_token):
    with pytest.raises(UnauthorizedError):
        await delete_post(client, '123', uuid8())
    with pytest.raises(UnauthorizedError):
        await restore_post(client, '123', uuid8())

    with pytest.raises(NotFoundError):
        await restore_post(client, access_token, uuid8())

    with pytest.raises(NotFoundError):
        await delete_post(client, access_token, uuid8())

    with pytest.raises(ForbiddenError):
        await delete_post(client, access_token, text_post_id)

    with pytest.raises(ForbiddenError):
        await restore_post(client, access_token, text_post_id)

    post = await create_post(client, access_token, 'for_test')

    await delete_post(client, access_token, post.id)

    await delete_post(client, access_token, post.id)

    await restore_post(client, access_token, post.id)
    await restore_post(client, access_token, post.id)

    await delete_post(client, access_token, post.id)


@pytest.mark.asyncio
async def test_delete_restore_post(client, access_token):
    with pytest.raises(UnauthorizedError):
        await like_post(client, '123', uuid8())
    with pytest.raises(UnauthorizedError):
        await delete_like_post(client, '123', uuid8())

    with pytest.raises(NotFoundError):
        await like_post(client, access_token, uuid8())
    with pytest.raises(NotFoundError):
        await delete_like_post(client, access_token, uuid8())

    await like_post(client, access_token, text_post_id)
    await like_post(client, access_token, text_post_id)
    await delete_like_post(client, access_token, text_post_id)
    await delete_like_post(client, access_token, text_post_id)


@pytest.mark.asyncio
async def test_pin_unpin_post(client, access_token):
    with pytest.raises(UnauthorizedError):
        await pin_post(client, '123', uuid8())

    with pytest.raises(NotFoundError):
        await pin_post(client, access_token, uuid8())

    with pytest.raises(ForbiddenError):
        await pin_post(client, access_token, text_post_id)

    post = await create_post(client, access_token, 'for_test')

    await pin_post(client, access_token, post.id)
    await pin_post(client, access_token, post.id)

    await unpin_post(client, access_token, post.id)

    with pytest.raises(NotPinedError):
        await unpin_post(client, access_token, uuid8())

    await delete_post(client, access_token, post.id)


@pytest.mark.asyncio
async def test_get_user_posts(client, access_token):
    with pytest.raises(UnauthorizedError):
        await get_posts_by_user(client, '123', uuid8())

    with pytest.raises(ParamsValidationError):
        await get_posts_by_user(client, access_token, 'nowkie', limit=0)

    await get_posts_by_user(client, access_token, 'nowkie', limit=1)
    await get_posts_by_user(client, access_token, 'nowkie', limit=50)

    with pytest.raises(ParamsValidationError):
        await get_posts_by_user(client, access_token, 'nowkie', limit=51)

    with pytest.raises(UserBlockedError):
        await get_posts_by_user(client, access_token, blocked_user)

    for sort in ['new', 'popular']:
        cursor = None
        while True:
            pagination, users = await get_posts_by_user(client, access_token, 'blue_cir', sort=sort, cursor=cursor)
            cursor = pagination.next_cursor
            if cursor is None:
                break

    await get_posts_by_user(client, access_token, UUID("5ee59a22-ae5a-49f9-9090-5a72e6285fad"))


@pytest.mark.asyncio
async def test_get_posts_by_user_liked(client, access_token):
    with pytest.raises(UnauthorizedError):
        await get_posts_by_user_liked(client, '123', uuid8())

    with pytest.raises(ParamsValidationError):
        await get_posts_by_user_liked(client, access_token, 'nowkie', limit=0)

    await get_posts_by_user_liked(client, access_token, 'nowkie', limit=1)
    await get_posts_by_user_liked(client, access_token, 'nowkie', limit=50)

    with pytest.raises(ParamsValidationError):
        await get_posts_by_user_liked(client, access_token, 'nowkie', limit=51)

    with pytest.raises(UserBlockedError):
        await get_posts_by_user_liked(client, access_token, blocked_user)

    cursor = None
    while True:
        pagination, users = await get_posts_by_user_liked(client, access_token, 'blue_cir', cursor=cursor)
        cursor = pagination.next_cursor
        if cursor is None:
            break

    await get_posts_by_user_liked(client, access_token, UUID("5ee59a22-ae5a-49f9-9090-5a72e6285fad"))


@pytest.mark.asyncio
async def test_get_posts_by_user_wall(client, access_token):
    with pytest.raises(UnauthorizedError):
        await get_posts_by_user_wall(client, '123', uuid8())

    with pytest.raises(ParamsValidationError):
        await get_posts_by_user_wall(client, access_token, 'nowkie', limit=0)

    await get_posts_by_user_wall(client, access_token, 'nowkie', limit=1)
    await get_posts_by_user_wall(client, access_token, 'nowkie', limit=50)

    with pytest.raises(ParamsValidationError):
        await get_posts_by_user_wall(client, access_token, 'nowkie', limit=51)

    with pytest.raises(UserBlockedError):
        await get_posts_by_user_wall(client, access_token, blocked_user)

    cursor = None
    while True:
        pagination, users = await get_posts_by_user_wall(client, access_token, 'blue_cir', cursor=cursor)
        cursor = pagination.next_cursor
        if cursor is None:
            break

    await get_posts_by_user_wall(client, access_token, UUID("5ee59a22-ae5a-49f9-9090-5a72e6285fad"))


@pytest.mark.asyncio
async def test_get_post_comments(client, access_token):
    with pytest.raises(UnauthorizedError):
        await get_post_comments(client, '123', uuid8())

    with pytest.raises(NotFoundError):
        await get_post_comments(client, access_token, uuid8())

    with pytest.raises(ParamsValidationError):
        await get_post_comments(client, access_token, post_with_all_type_comments, limit=0)

    await get_post_comments(client, access_token, post_with_all_type_comments, limit=1)
    await get_post_comments(client, access_token, post_with_all_type_comments, limit=500)

    with pytest.raises(ParamsValidationError):
        await get_post_comments(client, access_token, post_with_all_type_comments, limit=501)

    for sort in "popular", "newest", "oldest":
        cursor = None
        while True:
            pagination, users = await get_post_comments(
                client, access_token, post_with_all_type_comments, cursor, limit=2, sort=sort
            )
            cursor = pagination.next_cursor
            if cursor is None:
                break


@pytest.mark.asyncio
async def test_update_post(client, access_token):
    with pytest.raises(UnauthorizedError):
        await update_post(client, '123', uuid8(), '1')

    with pytest.raises(NotFoundError):
        await update_post(client, access_token, uuid8(), '1')

    with pytest.raises(ForbiddenError):
        await update_post(client, access_token, text_post_id, '1')

    with pytest.raises(ParamsValidationError):
        await update_post(client, access_token, text_post_id, '')

    with pytest.raises(ParamsValidationError):
        await update_post(client, access_token, text_post_id, '1' * 1001)

    post = await create_post(client, access_token, 'for_test')
    await update_post(client, access_token, post.id, '1' * 1000)
    await delete_post(client, access_token, post.id)


@pytest.mark.asyncio
async def test_repost(client, access_token):
    with pytest.raises(UnauthorizedError):
        await repost(client, '123', uuid8())

    with pytest.raises(NotFoundError):
        await repost(client, access_token, uuid8())

    with pytest.raises(NotFoundError):
        await repost(client, access_token, uuid8(), '1' * 1000)

    with pytest.raises(ParamsValidationError):
        await repost(client, access_token, uuid8(), '1' * 1001)


@pytest.mark.asyncio
async def test_create_post(client, access_token):
    with pytest.raises(UnauthorizedError):
        await create_post(client, '123')

    with pytest.raises(ValidationError):
        await create_post(client, access_token)

    post = await create_post(client, access_token, '1'*1000)
    await delete_post(client, access_token, post.id)
    with pytest.raises(ParamsValidationError):
        await create_post(client, access_token, '1'*1001)

    with pytest.raises(VideoRequiresVerificationError):
        await create_post(client, access_token, attachment_ids=[video_id])

    with pytest.raises(VideoRequiresVerificationError):
        await create_post(client, access_token, attachment_ids=[video_id]*10)

    with pytest.raises(ValidationError):
        await create_post(client, access_token, attachment_ids=[video_id]*11)

    with pytest.raises(ForbiddenError):
        await create_post(client, access_token, attachment_ids=[uuid8()])

    post = await create_post(client, access_token, attachment_ids=[audio_id, image_id])
    await delete_post(client, access_token, post.id)

    post = await create_post(client, access_token, attachment_ids=[image_id])
    await delete_post(client, access_token, post.id)

    spans = [
        Link(offset=0, length=5, url='https://yu.ru'),
        Monospace(offset=0, length=5),
        Strike(offset=0, length=5),
        Underline(offset=0, length=5),
        Bold(offset=0, length=5),
        Italic(offset=0, length=5),
        Spoiler(offset=0, length=5)
    ]
    post = await create_post(client, access_token, 'Эта ссылка куда?', spans=spans)
    await delete_post(post.id)

    with pytest.raises(ForbiddenError):
        await create_post(
            client, access_token, 'spand test',
            spans=[Monospace(offset=0, length=5)] * 100, attachment_ids=[uuid8()]
        )

    with pytest.raises(ParamsValidationError):
        await create_post(client, access_token, 'spand test', spans=[Monospace(offset=0, length=5)]*101)

    with pytest.raises(ParamsValidationError):
        await create_post(client, access_token, attachment_ids=[uuid8()], question='', options=['1', '2'])

    with pytest.raises(ForbiddenError):
         await create_post(client, access_token, attachment_ids=[uuid8()], question='1'*128, options=['1', '2'])

    with pytest.raises(ParamsValidationError):
        await create_post(client, access_token, attachment_ids=[uuid8()], question='1'*129, options=['1', '2'])

    with pytest.raises(ParamsValidationError):
        await create_post(client, access_token, attachment_ids=[uuid8()], question='1', options=['1'])

    with pytest.raises(ForbiddenError):
         await create_post(client, access_token, attachment_ids=[uuid8()], question='1', options=['1', '2'])

    with pytest.raises(ForbiddenError):
         await create_post(client, access_token, attachment_ids=[uuid8()], question='1', options=['1']*10)

    with pytest.raises(ParamsValidationError):
        await create_post(client, access_token, attachment_ids=[uuid8()], question='1', options=['1']*11)

    with pytest.raises(ParamsValidationError):
        await create_post(client, access_token, attachment_ids=[uuid8()], question='', options=['', '2'])

    with pytest.raises(ForbiddenError):
         await create_post(client, access_token, attachment_ids=[uuid8()], question='1'*128, options=['1'*32, '2'])

    with pytest.raises(ParamsValidationError):
        await create_post(client, access_token, attachment_ids=[uuid8()], question='1'*129, options=['1'*33, '2'])

    with pytest.raises(WallClosedError):
        await create_post(client, access_token, '1', wall_recipient_id=UUID("5ee59a22-ae5a-49f9-9090-5a72e6285fad"))

    with pytest.raises(NotFoundError):
        await create_post(client, access_token, '1', wall_recipient_id=uuid8())