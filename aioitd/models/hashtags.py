from uuid import UUID
from typing import Annotated

from pydantic import Field

from aioitd.models.base import ITDBaseModel


class Hashtag(ITDBaseModel):
    id: UUID
    name: str
    posts_count: Annotated[int, Field(alias="postsCount")]


__all__ = ['Hashtag']
