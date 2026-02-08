from uuid import uuid8

from aioitd import AsyncITDClient, TooLargeError, \
    ValidationError, NotFoundError
import unittest

from tests.setting import refresh_token, file_id, large_file_path, file_path


class TestFile(unittest.IsolatedAsyncioTestCase):
    async def test_too_large(self):
        try:
            async with AsyncITDClient(refresh_token) as client:
                with open(large_file_path, 'rb') as file:
                    file = await client.upload_file(file, validate_mimetype=False)
                    print(file)
        except TooLargeError:
            pass
        else:
            self.fail("TooLargeError не выброшено")

    async def test_mimetype_validation(self):
        try:
            async with AsyncITDClient(refresh_token) as client:
                with open("tests/abc.txt", 'rb') as file:
                    file = await client.upload_file(file)
        except ValidationError:
            pass
        else:
            self.fail("ValidationError не выброшено")

    async def test_upload_and_delete(self):
        async with AsyncITDClient(refresh_token) as client:
            with open(file_path, 'rb') as f:
                    file = await client.upload_file(f)
                    await client.delete_file(file.id)

    async def test_delete_not_found(self):
        try:
            async with AsyncITDClient(refresh_token) as client:
                await client.delete_file(uuid8())
        except NotFoundError:
            pass
        else:
            self.fail("NotFoundError не выброшен")

    async def test_get_file(self):
        async with AsyncITDClient(refresh_token) as client:
            file = await client.get_file(file_id)

    async def test_not_found(self):
        try:
            async with AsyncITDClient(refresh_token) as client:
                file = await client.get_file(uuid8())
        except NotFoundError:
            pass
        else:
            self.fail("NotFoundError не выброшен")


