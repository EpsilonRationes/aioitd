from datetime import datetime
import datetime as dt
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, BeforeValidator
from typing import Annotated, Literal
from uuid import UUID


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


class IntPagination(Pagination):
    next_cursor: Annotated[int | None, Field(alias="nextCursor")]


class TimePagination(Pagination):
    next_cursor: Annotated[ITDDatetime | None, Field(alias="nextCursor")]


class UUIDPagination(Pagination):
    next_cursor: Annotated[UUID | None, Field(alias="nextCursor")]


class BaseAuthor(ITDBaseModel):
    id: UUID
    username: str | None
    display_name: Annotated[str, Field(alias="displayName")]


class WallRecipient(BaseAuthor):
    avatar: str


class PinSlug(str, Enum):
    KIRILL67_202602_INFECTED = "kirill67_202602_infected"
    KIRILL67_202602_SURVIVOR = "kirill67_202602_survivor"

    def __str__(self):
        return self.value()


class Pin(ITDBaseModel):
    description: str
    name: str
    slug: PinSlug


class Author(WallRecipient):
    verified: bool
    pin: Pin | None


class OriginalPost(ITDBaseModel):
    id: UUID
    content: Annotated[str, Field(max_length=5000)]
    author: Author
    attachments: list[Annotated[
        ImagePostAttachmentWithoutFileName | AudioOrVideoPostAttachmentWithoutFileName, Field(discriminator="type")]]
    likes_count: Annotated[int, Field(alias="likesCount")]
    created_at: Annotated[ITDDatetime, Field(alias="createdAt")]
    comments_count: Annotated[int, Field(alias="commentsCount")]
    respot_count: Annotated[int, Field(alias="repostsCount")]
    views_count: Annotated[int, Field(alias="viewsCount")]
    spans: list[Span]

    is_deleted: Annotated[bool, Field(alias="isDeleted")]


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


class ImagePostAttachmentWithoutFileName(ITDBaseModel):
    id: UUID
    type: Literal["image"]
    url: str

    # thumbnail_url: Annotated[None | str, Field(alias="thumbnailUrl")]
    width: int
    height: int


class ImagePostAttachment(ImagePostAttachmentWithoutFileName):
    file_name: Annotated[str, Field(alias='filename')]
    mime_type: Annotated[str, Field(alias='mimeType')]
    size: int


class AudioOrVideoPostAttachmentWithoutFileName(ITDBaseModel):
    id: UUID
    type: Literal["audio", "video"]
    url: str
    # thumbnail_url: Annotated[None | str, Field(alias="thumbnailUrl")]
    width: None
    height: None


class AudioOrVideoPostAttachment(ITDBaseModel):
    id: UUID
    type: Literal["audio", "video"]
    url: str
    # thumbnail_url: Annotated[None | str, Field(alias="thumbnailUrl")]
    width: None
    height: None
    file_name: Annotated[str, Field(alias='filename')]
    mime_type: Annotated[str, Field(alias='mimeType')]
    size: int


class CreateAudioCommentAttachment(ITDBaseModel):
    filename: str
    id: UUID
    mimeType: str
    order: int
    size: int
    # thumbnailUrl: None | str
    type: Literal["audio"]
    url: str
    width: None
    height: None


class AudioCommentAttachment(CreateAudioCommentAttachment):
    duration: int


class CreateImageCommentAttachment(ITDBaseModel):
    filename: str
    id: UUID
    mimeType: str
    order: int
    size: int
    # thumbnailUrl: None | str
    type: Literal["image"]
    url: str
    width: int
    height: int


class ImageCommentAttachment(CreateImageCommentAttachment):
    duration: None


class CreateVideoCommentAttachment(ITDBaseModel):
    filename: str
    id: UUID
    mimeType: str
    order: int
    size: int
    # thumbnailUrl: None | str
    type: Literal["video"]
    url: str
    width: None
    height: None


class VideoCommentAttachment(CreateVideoCommentAttachment):
    duration: None


class Comment(BaseComment):
    replies: list[Reply]


class Reply(Comment):
    reply_to: Annotated[BaseAuthor, Field(alias="replyTo")]


class BaseSpan(ITDBaseModel):
    length: int
    offset: int


class Mention(BaseSpan):
    type: Literal['mention'] = 'mention'
    username: str


class HashTagSpan(BaseSpan):
    tag: str
    type: Literal['hashtag'] = 'hashtag'


class Monospace(BaseSpan):
    type: Literal["monospace"] = "monospace"


class Strike(BaseSpan):
    type: Literal["strike"] = "strike"


class Underline(BaseSpan):
    type: Literal["underline"] = "underline"


class Bold(BaseSpan):
    type: Literal["bold"] = "bold"


class Italic(BaseSpan):
    type: Literal["italic"] = "italic"


class Spoiler(BaseSpan):
    type: Literal["spoiler"] = "spoiler"


class Link(BaseSpan):
    type: Literal["link"] = "link"
    url: str


type Span = Annotated[
    Mention | HashTagSpan | Monospace | Strike | Underline | Bold | Italic | Spoiler | Link,
    Field(discriminator='type')
]


class User(WallRecipient):
    verified: bool
    followers_count: Annotated[int, Field(alias="followersCount")]
