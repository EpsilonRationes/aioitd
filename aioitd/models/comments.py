from typing import Annotated
from uuid import UUID

from pydantic import Field

from aioitd.models.base import ITDBaseModel, ITDDatetime, Attachment
from aioitd.models.users import UserStab, UserWithPin


class UpdateCommentResponse(ITDBaseModel):
    id: UUID
    content: str
    edited_at: Annotated[ITDDatetime | None, Field(alias="editedAt")]


class Comment(ITDBaseModel):
    id: UUID
    content: Annotated[str, Field(max_length=5000)]
    author: UserStab
    attachments: list[Attachment]
    likes_count: Annotated[int, Field(alias="likesCount")]
    created_at: Annotated[ITDDatetime, Field(alias="createdAt")]
    is_liked: Annotated[bool, Field(alias="isLiked")]
    replies_count: Annotated[int, Field(alias="repliesCount")]
    replies: list[Reply]


class Reply(Comment):
    reply_to: Annotated[UserWithPin, Field(alias="replyTo")]


__all__ = [UpdateCommentResponse, Comment, Reply]
