from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

from aioitd.models.base import AudioCommentAttachment, BaseAuthor, CreateAudioCommentAttachment, \
    CreateImageCommentAttachment, CreateVideoCommentAttachment, ITDBaseModel, ITDDatetime, ImageCommentAttachment, \
    VideoCommentAttachment, WallRecipient, Author


class BaseComment(ITDBaseModel):
    id: UUID
    content: Annotated[str, Field(max_length=5000)]
    author: Author
    attachments: list[
        Annotated[
            ImageCommentAttachment | AudioCommentAttachment | VideoCommentAttachment,
            Field(discriminator="type")
        ]
    ]
    likes_count: Annotated[int, Field(alias="likesCount")]
    created_at: Annotated[ITDDatetime, Field(alias="createdAt")]
    is_liked: Annotated[bool, Field(alias="isLiked")]
    replies_count: Annotated[int, Field(alias="repliesCount")]


class Comment(BaseComment):
    replies: list[Reply]


class CreateBaseComment(BaseComment):
    attachments: list[
        Annotated[
            ImageCommentAttachment | AudioCommentAttachment | VideoCommentAttachment,
            Field(discriminator="type")
        ]
    ]


class ReplyComment(CreateBaseComment):
    replies_count: Annotated[int, Field(alias="repliesCount")] = 0
    is_liked: Annotated[bool, Field(alias="isLiked")]
    reply_to: Annotated[None, Field(alias="replyTo")]


class Reply(Comment):
    reply_to: Annotated[BaseAuthor, Field(alias="replyTo")]


class UpdateCommentResponse(ITDBaseModel):
    id: UUID
    content: str
    edited_at: Annotated[ITDDatetime | None, Field(alias="editedAt")]
