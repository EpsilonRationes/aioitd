from aioitd.models.base import ITDBaseModel, ITDDatetime
from typing import Annotated
from uuid import UUID 
from pydantic import Field


class File(ITDBaseModel):
    id: UUID
    filename: str
    mime_type: Annotated[str, Field(alias='mimeType')]
    size: int
    url: str


class GetFile(File):
    created_at: Annotated[ITDDatetime, Field(alias="createdAt")]
    