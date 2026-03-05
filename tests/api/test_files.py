from uuid import UUID

import pytest
from tests.api import client, access_token

from aioitd import UnauthorizedError, NotFoundError, ContentModerationError, \
    ValidationError, TooLargeError
from aioitd.api.files import get_file, delete_file, upload_file

not_me_file = UUID('f0ec8a7a-9c7f-48f6-b341-7b94db799329')


@pytest.mark.asyncio
async def test_files(client, access_token):
    with pytest.raises(UnauthorizedError):
        with open('tests/image.jpg', 'rb') as file:
            await upload_file(client, "123", file)

    with open('tests/image.jpg', 'rb') as file:
        image = await upload_file(client, access_token, file)

    with pytest.raises(NotFoundError):
        await get_file(client, access_token, image.id)

    with open('tests/video.mov', 'rb') as file:
        video = await upload_file(client, access_token, file)

    with open('tests/audio.mp3', 'rb') as file:
        audio = await upload_file(client, access_token, file)

    with pytest.raises(UnauthorizedError):
        await delete_file(client, '123', image.id)

    await delete_file(client, access_token, image.id)
    await delete_file(client, access_token, video.id)
    await delete_file(client, access_token, audio.id)

    with pytest.raises(NotFoundError):
        await delete_file(client, access_token, image.id)
    with pytest.raises(NotFoundError):
        await delete_file(client, access_token, not_me_file)

    with pytest.raises(ContentModerationError):
        with open('tests/abc.png', 'rb') as file:
            await upload_file(client, access_token, file)

    with pytest.raises(ValidationError):
        with open('tests/abc.txt', 'rb') as file:
            await upload_file(client, access_token, file)

    with pytest.raises(TooLargeError):
        with open("tests/large_file.mp4", 'rb') as file:
            await upload_file(client, access_token, file)
