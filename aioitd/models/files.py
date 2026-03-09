from enum import Enum
from typing import Annotated
from uuid import UUID

from pydantic import Field

from aioitd.models.base import ITDBaseModel, ITDDatetime


class File(ITDBaseModel):
    id: UUID
    filename: str
    mime_type: Annotated[str, Field(alias='mimeType')]
    size: int
    url: str


class GetFile(File):
    created_at: Annotated[ITDDatetime, Field(alias="createdAt")]


class AttachmentType(str, Enum):
    IMAGE = 'image'
    AUDIO = 'audio'
    VIDEO = 'video'


class Attachment(File):
    type: AttachmentType
    width: int | None = None
    height: int | None = None
    filename: Annotated[str | None, Field(alias='filename')] = None
    mime_type: Annotated[str | None, Field(alias='mimeType')] = None
    size: int | None = None
    duration: int | None = None
    order: int | None = None


__all__ = ['File', 'GetFile', 'AttachmentType', 'Attachment']
