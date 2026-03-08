from typing import Annotated
from uuid import UUID

from pydantic import Field

from aioitd.models.base import ITDBaseModel, ITDDatetime
from aioitd.models.files import Attachment
from aioitd.models.users import UserWithPin, UserStab


class UpdateCommentResponse(ITDBaseModel):
    id: UUID
    content: str
    edited_at: Annotated[ITDDatetime | None, Field(alias="editedAt")]


class Comment(ITDBaseModel):
    id: UUID
    content: Annotated[str, Field(max_length=5000)]
    author: UserWithPin
    attachments: list[Attachment]
    likes_count: Annotated[int, Field(alias="likesCount")]
    created_at: Annotated[ITDDatetime, Field(alias="createdAt")]
    is_liked: Annotated[bool, Field(alias="isLiked")]
    replies_count: Annotated[int, Field(alias="repliesCount")]
    replies: list[Reply]


class Reply(Comment):
    reply_to: Annotated[UserStab, Field(alias="replyTo")]


__all__ = ['UpdateCommentResponse', 'Comment', 'Reply']
