from datetime import datetime
import datetime as dt
from enum import Enum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, BeforeValidator


def datetime_from_itd_format(val: str) -> datetime:
    if 'Z' in val:
        return datetime.fromisoformat(val)
    else:
        return datetime.strptime(val + ':00', "%Y-%m-%d %H:%M:%S.%f%z")


def datetime_to_itd_format(val: datetime) -> str:
    if val.tzinfo == dt.timezone.utc:
        return val.isoformat()[:-9] + "Z"
    else:
        return val.strftime("%Y-%m-%d %H:%M:%S.%f%z")[:-2]


ITDDatetime = Annotated[
    datetime,
    BeforeValidator(lambda x: datetime_from_itd_format(x) if isinstance(x, str) else x)
]


class ITDBaseModel(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        json_encoders={
            datetime: datetime_to_itd_format
        }
    )


class Pagination(ITDBaseModel):
    limit: int
    has_more: Annotated[bool, Field(alias="hasMore")]
    next_cursor: Annotated[str | None, Field(alias="nextCursor")]


class TotalPagination(ITDBaseModel):
    total: int
    has_more: Annotated[bool, Field(alias="hasMore")]
    next_cursor: Annotated[str | None, Field(alias="nextCursor")]


class PagePagination(ITDBaseModel):
    total: int
    has_more: Annotated[bool, Field(alias="hasMore")]
    limit: int
    page: int


class AttachmentType(str, Enum):
    IMAGE = 'image'
    AUDIO = 'audio'
    VIDEO = 'video'


class Attachment(ITDBaseModel):
    id: UUID
    type: AttachmentType
    url: str
    width: int | None = None
    height: int | None = None
    file_name: Annotated[str | None, Field(alias='filename')] = None
    mime_type: Annotated[str | None, Field(alias='mimeType')] = None
    size: int | None = None
    duration: int | None = None
    order: int | None = None


__all__ = [Attachment, AttachmentType, PagePagination, Pagination, TotalPagination, ITDDatetime, ITDDatetime,
           datetime_from_itd_format, datetime_to_itd_format]
