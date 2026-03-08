from uuid import UUID
from typing import IO
import warnings

import httpx

from aioitd.fetch import delete, get, post, add_bearer
from aioitd.models.files import GetFile, File


async def get_file(
        client: httpx.AsyncClient,
        access_token: str,
        file_id: UUID | str,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> GetFile:
    """Получить файл.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        file_id: UUID файла
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации

    """
    warnings.warn(
        "похоже этот endpoint удалили",
        DeprecationWarning,
        stacklevel=2
    )
    response = await get(
        client,
        f"https://{domain}/api/files/{file_id}",
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()
    return GetFile(**data)


async def upload_file(
        client: httpx.AsyncClient,
        access_token: str,
        file: IO[bytes],
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> File:
    """Загрузить файл.

    Args:
        client: httpx.AsyncClient
        access_token: access токен
        file: файл
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        ValidationError: недопустимый тип файла
        TooLargeError: размер запроса слишком большой
        UploadError: ошибка загрузки файла
        ContentModerationError: Не далось проверить файл

    Examples:

        with open('file.png', 'rb') as file:
            file = await upload_file(client, access_token, file)
    """
    response = await post(
        client,
        f"https://{domain}/api/files/upload",
        files={'file': file}, timeout=1000,
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()
    return File(**data)


async def delete_file(
        client: httpx.AsyncClient,
        access_token: str,
        file_id: UUID,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> None:
    """Удалить файл.

    Args:
        client: httpx.AsyncClient
        access_token: access токен
        file_id: UUID файла
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: Файл не найден, или нет прав доступа к нему
    """
    await delete(
        client,
        f"https://{domain}/api/files/{file_id}",
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )


__all__ = [get_file, upload_file, delete_file]
