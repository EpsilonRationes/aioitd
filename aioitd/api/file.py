from json import JSONDecodeError
from typing import IO, Any
from dataclasses import dataclass, field
from uuid import UUID
from datetime import datetime

import httpx

from aioitd import UnauthorizedError, UnknowError
from aioitd.api.auth import add_bearer


@dataclass
class File:
    """Файл ИТД.

    Attributes:
        id: UUID файла
        filename: имя файла
        url: адрес файла
        mime_type: mime тип (https://developer.mozilla.org/ru/docs/Web/HTTP/Guides/MIME_types)
        size: размер файла в байтах
        created_at: время загрузки
    """
    id: UUID
    filename: str
    url: str
    mime_type: str
    size: int
    created_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> File:
        return File(
            id=UUID(data['id']),
            filename=data['filename'],
            url=data['url'],
            mime_type=data['mimeType'],
            size=data['size'],
            created_at=datetime.fromisoformat(data['createdAt'].replace('Z', '+00:00')) if data['createdAt']
                        else datetime.now()
        )


# Если строка уже в формате ISO 8601
date_string = '2026-02-06T06:59:27.948Z'


async def upload_file(session: httpx.AsyncClient, access_token: str, file: IO[bytes]) -> File:
    """Загрузить файл.

    Args:
        session: httpx.AsyncClient
        access_token: access токен
        file: файл

    Raises:
        UnauthorizedError: неверный access токен
    """
    files = {'file': file}
    result = await session.post(
        "https://xn--d1ah4a.com/api/files/upload",
        files=files,
        headers={"authorization": add_bearer(access_token)}
    )
    if result.text == "UNAUTHORIZED":
        raise UnauthorizedError

    response = result.json()
    return File.from_json(response)


async def get_file(session: httpx.AsyncClient, access_token: str, file_id: UUID | str) -> File:
    """Получить файл.

    Args:
        session: httpx.AsyncClient
        access_token: access токен
        file_id: UUID файла

    Raises:
        UnauthorizedError: неверный access токен
    """
    result = await session.get(
        f"https://xn--d1ah4a.com/api/files/{file_id}", headers={"authorization": add_bearer(access_token)}
    )

    if result.text == "UNAUTHORIZED":
        raise UnauthorizedError

    response = result.json()

    return File.from_json(response)


class FileNotFound(ValueError):
    def __str__(self):
        return f"Файл не найден, или нет прав доступа к нему"


async def delete_file(session: httpx.AsyncClient, access_token: str, file_id: UUID | str):
    """Удалить файл

    Args:
        session: httpx.AsyncClient
        access_token: access токен
        file_id: UUID файла

    Raises:
        UnauthorizedError: неверный access токен
        FileNotFoundError: Файл не найден, или нет прав доступа к нему
    """
    if isinstance(file_id, str):
        file_id = UUID(file_id)
    result = await session.delete(
        f"https://xn--d1ah4a.com/api/files/{file_id}", headers={"authorization": add_bearer(access_token)}
    )

    if result.text == "UNAUTHORIZED":
        raise UnauthorizedError

    try:
        response = result.json()
        if 'error' in response:
            if response['error']['code'] == 'NOT_FOUND':
                raise FileNotFoundError
            else:
                raise UnknowError(code=response['error']['code'], message=response['error']['message'])
    except JSONDecodeError:
        pass
