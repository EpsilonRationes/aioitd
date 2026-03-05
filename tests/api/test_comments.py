import asyncio

import pytest
from uuid import uuid8, UUID

from aioitd import UnauthorizedError, NotFoundError, ValidationError, ParamsValidationError, ITDError, ForbiddenError
from tests.api import client, access_token

from aioitd.api.comments import comment, replies, like_comment, delete_like_comment, restore_comment, delete_comment, \
    edit_comment

post_id = UUID("f9e1d062-ef17-484b-b02e-11fd0b9cac94")
file_id = UUID("f4399b89-49a1-4068-a0f2-0d8dfd22a81e")
image_id = UUID("a3c4a9fb-4870-49db-b7f1-5358fa0bc27f")
audio_id = UUID("ce120fab-93b8-4ab4-b0b4-543b989e8a1d")
video_id = UUID("9ba2e97f-f986-4a06-9576-81d3961ba342")
not_me_image = UUID("45f8cb85-f1c9-4aa7-a69d-449351e7b4a5")

comment_id = UUID("01645b06-63c3-48d5-b161-8e1de1c651cf")
not_me_comment_id = UUID("f6200a84-18b6-4da7-a53a-941e555a7841")


@pytest.mark.asyncio
async def test_comment(client, access_token):
    with pytest.raises(UnauthorizedError):
        c = await comment(client, '123', uuid8(), content="123")

    with pytest.raises(NotFoundError):
        c = await comment(client, access_token, uuid8(), content="123")

    with pytest.raises(ValidationError):
        c = await comment(client, access_token, post_id)

    c = await comment(client, access_token, post_id, attachment_ids=[file_id])

    with pytest.raises(ITDError):
        c = await comment(client, access_token, post_id, attachment_ids=[not_me_image] * 2)
    await asyncio.sleep(60)
    with pytest.raises(ITDError):
        c = await comment(client, access_token, post_id, attachment_ids=[uuid8()])

    c = await comment(client, access_token, post_id, attachment_ids=[file_id, audio_id, image_id, video_id])
    with pytest.raises(ParamsValidationError):
        c = await comment(client, access_token, post_id, attachment_ids=[file_id] * 5)

    await comment(client, access_token, post_id, content="0" * 1000)
    with pytest.raises(ParamsValidationError):
        c = await comment(client, access_token, post_id, content="0" * 1001)


@pytest.mark.asyncio
async def test_replies(client, access_token):
    with pytest.raises(UnauthorizedError):
        c = await replies(client, "123", comment_id)

    with pytest.raises(NotFoundError):
        await replies(client, access_token, uuid8(), "content")

    with pytest.raises(ValidationError):
        await replies(client, access_token, comment_id)

    with pytest.raises(ITDError):
        await replies(client, access_token, comment_id, attachment_ids=[uuid8()])

    await replies(client, access_token, comment_id, attachment_ids=[file_id, audio_id, image_id, video_id])
    await asyncio.sleep(60)
    with pytest.raises(ParamsValidationError):
        await replies(client, access_token, comment_id,
                      attachment_ids=[file_id, audio_id, image_id, video_id, not_me_image])

    await replies(client, access_token, comment_id, content='1' * 1000)

    with pytest.raises(ParamsValidationError):
        await replies(client, access_token, comment_id, content='1' * 1001)

    await replies(client, access_token, comment_id, content="0", replay_to_user_id=uuid8())


@pytest.mark.asyncio
async def test_like_comment(client, access_token):
    with pytest.raises(UnauthorizedError):
        await like_comment(client, '123', comment_id)

    with pytest.raises(UnauthorizedError):
        await delete_like_comment(client, '123', comment_id)

    await like_comment(client, access_token, comment_id)
    await like_comment(client, access_token, comment_id)

    await delete_like_comment(client, access_token, comment_id)
    await delete_like_comment(client, access_token, comment_id)

    with pytest.raises(NotFoundError):
        await like_comment(client, access_token, uuid8())

    with pytest.raises(NotFoundError):
        await delete_like_comment(client, access_token, uuid8())


@pytest.mark.asyncio
async def test_delete_restore_comment(client, access_token):
    with pytest.raises(UnauthorizedError):
        await delete_comment(client, '123', comment_id)

    with pytest.raises(UnauthorizedError):
        await restore_comment(client, '123', comment_id)

    id = (await comment(client, access_token, post_id, content="for_test")).id

    await delete_comment(client, access_token, id)
    await delete_comment(client, access_token, id)

    await restore_comment(client, access_token, id)
    await restore_comment(client, access_token, id)

    with pytest.raises(NotFoundError):
        await restore_comment(client, access_token, uuid8())

    with pytest.raises(NotFoundError):
        await delete_comment(client, access_token, uuid8())

    with pytest.raises(ForbiddenError):
        await delete_comment(client, access_token, not_me_comment_id)

    with pytest.raises(ForbiddenError):
        await restore_comment(client, access_token, not_me_comment_id)


@pytest.mark.asyncio
async def test_update_comment(client, access_token):
    with pytest.raises(UnauthorizedError):
        await edit_comment(client, '123', comment_id, content='1')

    id = (await comment(client, access_token, post_id, content="for_test")).id

    with pytest.raises(ParamsValidationError):
        await edit_comment(client, access_token, id, content='')

    await edit_comment(client, access_token, id, content='1')

    with pytest.raises(ParamsValidationError):
        await edit_comment(client, access_token, id, content='1' * 1001)

    with pytest.raises(ForbiddenError):
        await edit_comment(client, access_token, not_me_comment_id, content='1')
