from uuid import UUID
from typing import Annotated

from pydantic import Field

from aioitd.models.base import ITDBaseModel, ImagePostAttachment, AudioOrVideoPostAttachment, Span, WallRecipient, \
    OriginalPost, ITDDatetime, Comment, Author


class Hashtag(ITDBaseModel):
    id: UUID
    name: str
    posts_count: Annotated[int, Field(alias="postsCount")]


class HashtagPost(ITDBaseModel):
    id: UUID
    content: Annotated[str, Field(max_length=5000)]
    author: Author
    attachments: list[Annotated[ImagePostAttachment | AudioOrVideoPostAttachment, Field(discriminator="type")]]
    likes_count: Annotated[int, Field(alias="likesCount")]
    created_at: Annotated[ITDDatetime, Field(alias="createdAt")]

    comments_count: Annotated[int, Field(alias="commentsCount")]
    respot_count: Annotated[int, Field(alias="repostsCount")]
    views_count: Annotated[int, Field(alias="viewsCount")]
    spans: list[Span]

    is_liked: Annotated[bool, Field(alias="isLiked")]
    comments: list[Comment]

    wall_recipient_id: Annotated[None | UUID, Field(alias="wallRecipientId")] = None
    wall_recipient: Annotated[None | WallRecipient, Field(alias="wallRecipient")]

    is_reposted: Annotated[bool, Field(alias="isReposted")]
    original_post: Annotated[OriginalPost | None, Field(alias="originalPost")]

    is_owner: Annotated[bool, Field(alias="isOwner")]

    dominant_emoji: Annotated[str | None, Field(alias="dominantEmoji")]
