from enum import Enum
from uuid import UUID
from typing import Annotated, Literal

from pydantic import Field

from aioitd.models.base import ITDDatetime, ITDBaseModel
from aioitd.models.files import Attachment
from aioitd.models.users import UserWithPin, UserWithAvatar


class Option(ITDBaseModel):
    id: UUID
    position: int
    text: str
    votest_count: Annotated[int, Field(alias="votesCount")]


class Poll(ITDBaseModel):
    id: UUID
    question: str
    total_votes: Annotated[int, Field(alias="totalVotes")]
    options: list[Option]
    multiple_choice: Annotated[bool, Field(alias="multipleChoice")]
    post_id: Annotated[UUID, Field(alias="postId")]
    has_voted: Annotated[bool, Field(alias="hasVoted")]
    created_at: Annotated[ITDDatetime, Field(alias="createdAt")]
    voted_option_ids: Annotated[list[UUID], Field(alias="votedOptionIds")]


class UpdatePostResponse(ITDBaseModel):
    id: UUID
    content: str
    spans: list[Span]
    updated_at: Annotated[ITDDatetime | None, Field(alias="updatedAt")]


class SpanType(str, Enum):
    MENTION = 'mention'
    HASHTAG = 'hashtag'
    MONOSPACE = 'monospace'
    STRIKE = 'strike'
    UNDERLINE = 'underline'
    BOLD = 'bold'
    ITALIC = 'italic'
    SPOILER = 'spoiler'
    LINK = 'link'


class BaseSpan(ITDBaseModel):
    length: int
    offset: int
    type: SpanType


class Mention(BaseSpan):
    type: Literal[SpanType.MENTION] = SpanType.MENTION
    username: str


class HashTagSpan(BaseSpan):
    tag: str
    type: Literal[SpanType.HASHTAG] = SpanType.HASHTAG


class Monospace(BaseSpan):
    type: Literal[SpanType.MONOSPACE] = SpanType.MONOSPACE


class Strike(BaseSpan):
    type: Literal[SpanType.STRIKE] = SpanType.STRIKE


class Underline(BaseSpan):
    type: Literal[SpanType.UNDERLINE] = SpanType.UNDERLINE


class Bold(BaseSpan):
    type: Literal[SpanType.BOLD] = SpanType.BOLD


class Italic(BaseSpan):
    type: Literal[SpanType.ITALIC] = SpanType.ITALIC


class Spoiler(BaseSpan):
    type: Literal[SpanType.SPOILER] = SpanType.SPOILER


class Link(BaseSpan):
    type: Literal[SpanType.LINK] = SpanType.LINK
    url: str


type Span = Annotated[
    Mention | HashTagSpan | Monospace | Strike | Underline | Bold | Italic | Spoiler | Link,
    Field(discriminator='type')
]


class BasePost(ITDBaseModel):
    id: UUID
    content: Annotated[str, Field(max_length=5000)]
    author: UserWithPin
    attachments: list[Attachment]
    likes_count: Annotated[int, Field(alias="likesCount")]
    created_at: Annotated[ITDDatetime, Field(alias="createdAt")]
    comments_count: Annotated[int, Field(alias="commentsCount")]
    respot_count: Annotated[int, Field(alias="repostsCount")]
    views_count: Annotated[int, Field(alias="viewsCount")]
    spans: list[Span]


class OriginalPost(BasePost):
    is_deleted: Annotated[bool, Field(alias="isDeleted")]


class Post(BasePost):
    is_liked: Annotated[bool, Field(alias="isLiked")]
    wall_recipient_id: Annotated[None | UUID, Field(alias="wallRecipientId")]
    is_viewed: Annotated[bool, Field(alias="isViewed")]
    is_reposted: Annotated[bool, Field(alias="isReposted")]
    poll: Poll | None
    is_owner: Annotated[bool, Field(alias="isOwner")]
    original_post: Annotated[OriginalPost | None, Field(alias="originalPost")]
    dominant_emoji: Annotated[str | None, Field(alias="dominantEmoji")]
    edited_at: Annotated[ITDDatetime | None, Field(alias="editedAt")]
    wall_recipient: Annotated[None | UserWithAvatar, Field(alias="wallRecipient")]  # везде кроме лайков норм


__all__ = [
    'Option', 'Poll', 'UpdatePostResponse', 'Post', 'OriginalPost', 'Span', 'BaseSpan', 'Mention', 'HashTagSpan',
    'Monospace', 'Strike', 'Underline', 'Bold', 'Italic', 'Spoiler', 'Link', 'BasePost'
]
