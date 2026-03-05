from datetime import datetime
import datetime as dt

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


class Pin(ITDBaseModel):
    description: str
    name: str
    slug: str

class Author(WallRecipient):
    verified: bool
    pin: Pin | None




class OriginalPost(ITDBaseModel):
    id: UUID
    content: Annotated[str, Field(max_length=5000)]
    author: Author
    attachments: list[Annotated[ImagePostAttachment | InvalidPostAttachment, Field(discriminator="type")]]
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


class ImagePostAttachment(ITDBaseModel):
    id: UUID
    type: Literal["image"]
    url: str
    file_name: Annotated[str, Field(alias='filename')]
    mime_type: Annotated[str, Field(alias='mimeType')]
    # thumbnail_url: Annotated[None | str, Field(alias="thumbnailUrl")]
    width: int
    height: int
    size: int


class InvalidPostAttachment(ITDBaseModel):
    id: UUID
    type: Literal["audio", "video"]
    url: str
    # thumbnail_url: Annotated[None | str, Field(alias="thumbnailUrl")]
    width: None
    height: None

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


class MentionSpan(BaseSpan):
    type: Literal['mention']
    username: str


class HashTagSpan(BaseSpan):
    tag: str
    type: Literal['hashtag'] = 'hashtag'


class MonospaceSpan(BaseSpan):
    type: Literal["monospace"] = "monospace"


class StrikeSpan(BaseSpan):
    type: Literal["strike"] = "strike"


class UnderlineSpan(BaseSpan):
    type: Literal["underline"] = "underline"


class BoldSpan(BaseSpan):
    type: Literal["bold"] = "bold"


class ItalicSpan(BaseSpan):
    type: Literal["italic"] = "italic"


class SpoilerSpan(BaseSpan):
    type: Literal["spoiler"] = "spoiler"


class LinkSpan(BaseSpan):
    type: Literal["link"] = "link"
    url: str


type Span = Annotated[
    MentionSpan | HashTagSpan | MonospaceSpan | StrikeSpan | UnderlineSpan | BoldSpan | ItalicSpan | SpoilerSpan | LinkSpan,
    Field(discriminator='type')
]

class User(WallRecipient):
    verified: bool
    followers_count: Annotated[int, Field(alias="followersCount")]