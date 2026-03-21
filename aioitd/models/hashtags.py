from uuid import UUID
from typing import Annotated

from pydantic import Field

from aioitd.objects.hashtags import HashtagRef


class Hashtag(HashtagRef):
    id: UUID
    name: str
    posts_count: Annotated[int, Field(alias="postsCount")]


__all__ = ['Hashtag']
