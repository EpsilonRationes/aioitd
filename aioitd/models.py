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


class Pin(ITDBaseModel):
    description: str
    name: str
    slug: str


class BaseAuthor(ITDBaseModel):
    id: UUID
    username: str
    display_name: Annotated[str, Field(alias="displayName")]


class WallRecipient(BaseAuthor):
    avatar: str


class VerifiedUser(WallRecipient):
    verified: bool


class Author(VerifiedUser):
    pin: Pin | None


class AuthorWithoutId(ITDBaseModel):
    avatar: str
    pin: Pin | None
    verified: bool
    username: str
    display_name: Annotated[str, Field(alias="displayName")]


class ImagePostAttachment(ITDBaseModel):
    id: UUID
    type: Literal["image"]
    url: str
    thumbnail_url: Annotated[None | str, Field(alias="thumbnailUrl")]
    width: int
    height: int


class InvalidPostAttachment(ITDBaseModel):
    id: UUID
    type: Literal["audio", "video"]
    url: str
    thumbnail_url: Annotated[None | str, Field(alias="thumbnailUrl")]
    width: None
    height: None


class AudioCommentAttachment(ITDBaseModel):
    duration: int
    filename: str
    id: UUID
    mimeType: str
    order: int
    size: int
    thumbnailUrl: None | str
    type: Literal["audio"]
    url: str
    width: None
    height: None


class ImageCommentAttachment(ITDBaseModel):
    duration: None
    filename: str
    id: UUID
    mimeType: str
    order: int
    size: int
    thumbnailUrl: None | str
    type: Literal["image"]
    url: str
    width: int
    height: int


class VideoCommentAttachment(ITDBaseModel):
    duration: None
    filename: str
    id: UUID
    mimeType: str
    order: int
    size: int
    thumbnailUrl: None | str
    type: Literal["video"]
    url: str
    width: None
    height: None


class BasePost(ITDBaseModel):
    id: UUID
    content: Annotated[str, Field(max_length=5000)]
    author: Author
    attachments: list[Annotated[ImagePostAttachment | InvalidPostAttachment, Field(discriminator="type")]]
    likes_count: Annotated[int, Field(alias="likesCount")]
    created_at: Annotated[ITDDatetime, Field(alias="createdAt")]


class BasePostWithoutAuthorId(ITDBaseModel):
    id: UUID
    content: Annotated[str, Field(max_length=5000)]
    author: AuthorWithoutId
    attachments: list[Annotated[ImagePostAttachment | InvalidPostAttachment, Field(discriminator="type")]]
    likes_count: Annotated[int, Field(alias="likesCount")]
    created_at: Annotated[ITDDatetime, Field(alias="createdAt")]


class Span(ITDBaseModel):
    length: int
    tag: str
    type: Literal['hashtag']
    offset: int


class Counts(ITDBaseModel):
    comments_count: Annotated[int, Field(alias="commentsCount")]
    respot_count: Annotated[int, Field(alias="repostsCount")]
    views_count: Annotated[int, Field(alias="viewsCount")]
    spans: list[Span]


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


class ReplyComment(BasePost):
    is_liked: Annotated[bool, Field(alias="isLiked")]
    reply_to: Annotated[None, Field(alias="replyTo")]


class Reply(Comment):
    reply_to: Annotated[BaseAuthor, Field(alias="replyTo")]


class OriginalPost(BasePost, Counts):
    is_deleted: Annotated[bool, Field(alias="isDeleted")]


class Post(BasePost, Counts):
    is_liked: Annotated[bool, Field(alias="isLiked")]
    is_viewed: Annotated[bool, Field(alias="isViewed")]

    wall_recipient_id: Annotated[None | UUID, Field(alias="wallRecipientId")]

    is_reposted: Annotated[bool, Field(alias="isReposted")]
    original_post: Annotated[OriginalPost | None, Field(alias="originalPost")]

    is_owner: Annotated[bool, Field(alias="isOwner")]


class PostWithoutAuthorId(BasePostWithoutAuthorId, Counts):
    is_liked: Annotated[bool, Field(alias="isLiked")]

    wall_recipient_id: Annotated[None | UUID, Field(alias="wallRecipientId")]

    is_reposted: Annotated[bool, Field(alias="isReposted")]
    original_post: Annotated[OriginalPost | None, Field(alias="originalPost")]

    is_owner: Annotated[bool, Field(alias="isOwner")]


class PopularPost(Post):
    author_id: Annotated[UUID, Field(alias="authorId")]


class UserPost(Post):
    wall_recipient: Annotated[None | WallRecipient, Field(alias="wallRecipient")]


class UserPostWithoutAuthorId(BasePostWithoutAuthorId, Counts):
    is_liked: Annotated[bool, Field(alias="isLiked")]

    wall_recipient_id: Annotated[None | UUID, Field(alias="wallRecipientId")]

    is_reposted: Annotated[bool, Field(alias="isReposted")]

    is_owner: Annotated[bool, Field(alias="isOwner")]

    wall_recipient: Annotated[None | WallRecipient, Field(alias="wallRecipient")]


class FullPost(UserPost):
    comments: list[Comment]


class Pagination(ITDBaseModel):
    limit: int
    has_more: Annotated[bool, Field(alias="hasMore")]
    next_cursor: Annotated[str, Field(alias="nextCursor")]


class IntPagination(Pagination):
    next_cursor: Annotated[int | None, Field(alias="nextCursor")]


class TimePagination(Pagination):
    next_cursor: Annotated[ITDDatetime | None, Field(alias="nextCursor")]


class UUIDPagination(Pagination):
    next_cursor: Annotated[UUID | None, Field(alias="nextCursor")]


class CommentPagination(ITDBaseModel):
    total: int
    has_more: Annotated[bool, Field(alias="hasMore")]
    next_cursor: Annotated[str | None, Field(alias="nextCursor")]


class IntCommentPagination(CommentPagination):
    next_cursor: Annotated[int | None, Field(alias="nextCursor")]


class UUIDCommentPagination(CommentPagination):
    next_cursor: Annotated[UUID | None, Field(alias="nextCursor")]


class UpdatePostResponse(ITDBaseModel):
    id: UUID
    content: str
    spans: list[Span]
    updated_at: Annotated[datetime | None, Field(alias="updatedAt")]


class Hashtag(ITDBaseModel):
    id: UUID
    name: str
    posts_count: Annotated[int, Field(alias="postsCount")]


class User(WallRecipient):
    verified: bool
    followers_count: Annotated[int, Field(alias="followersCount")]


class Report(ITDBaseModel):
    id: UUID
    created_at: Annotated[datetime, Field(alias="createdAt")]


class Me(BaseAuthor):
    bio: str
    update_at: Annotated[datetime, Field(alias="updatedAt")]


class BaseFullUser(Author):
    bio: str
    banner: str | None
    created_at: Annotated[datetime, Field(alias="createdAt")]
    posts_count: Annotated[int, Field(alias="postsCount")]
    wall_access: Annotated[Literal["everyone", "followers", "mutual", "nobody"], Field(alias="wallAccess")]
    following_count: Annotated[int, Field(alias="followingCount")]
    followers_count: Annotated[int, Field(alias="followersCount")]
    likes_visibility: Annotated[str, Field(alias="likesVisibility")]


class FullMe(BaseFullUser):
    is_private: Annotated[bool, Field(alias="isPrivate")]
    wall_access: Annotated[Literal["everyone", "followers", "mutual", "nobody"], Field(alias="wallAccess")]


class FullUser(FullMe):
    is_followed_by: Annotated[bool, Field(alias="isFollowedBy")]
    is_following: Annotated[bool, Field(alias="isFollowing")]
    pinned_post_id: Annotated[UUID | None, Field(alias="pinnedPostId")]


class FollowUser(WallRecipient):
    verified: bool
    is_following: Annotated[bool, Field(alias="isFollowing")]


class FollowPagination(ITDBaseModel):
    total: int
    has_more: Annotated[bool, Field(alias="hasMore")]
    limit: int
    page: int


class Clan(ITDBaseModel):
    avatar: str
    member_count: Annotated[int, Field(alias="memberCount")]


class PinWithDate(Pin):
    granted_at: Annotated[datetime, Field(alias="grantedAt")]


class Notification(ITDBaseModel):
    id: UUID
    created_at: Annotated[datetime, Field(alias="createdAt")]
    preview: str | None
    read: bool
    actor: WallRecipient
    read_at: Annotated[datetime | None, Field(alias="readAt")]
    target_id: Annotated[UUID | None, Field(alias="targetId")]
    target_type: Annotated[Literal['post'] | None, Field(alias="targetType")]
    type: Literal[
        'reply', 'like', 'wall_post', 'follow', 'comment', 'repost', 'mention', 'verification_approved', 'verification_rejected'
    ]


class File(ITDBaseModel):
    id: UUID
    filename: str
    mime_type: Annotated[str, Field(alias='mimeType')]
    size: int
    url: str


class GetFile(File):
    created_at: Annotated[datetime, Field(alias="createdAt")]


class Privacy(ITDBaseModel):
    is_private: Annotated[bool, Field(alias="isPrivate")]
    likes_visibility: Annotated[Literal["everyone", "followers", "mutual", "nobody"], Field(alias='likesVisibility')]
    wall_access: Annotated[Literal["everyone", "followers", "mutual", "nobody"], Field(alias='wallAccess')]


class UserWithRole(VerifiedUser):
    roles: list[str | Literal["user"]]
    bio: str


class Profile(ITDBaseModel):
    authenticated: bool
    banned: bool
    user: UserWithRole


class BlockedUser(Author):
    is_blocked_by_me: Annotated[bool, Field(alias="isBlockedByMe")]


class BlockedAuthor(VerifiedUser):
    blocked_at: Annotated[datetime, Field(alias="blockedAt")]


class UserBlockMe(Author):
    is_blocked_by_them: Annotated[bool, Field(alias="isBlockedByThem")]
    is_private: Annotated[bool, Field(alias="isPrivate")]
    s_followed_by: Annotated[bool, Field(alias="isFollowedBy")]
    is_following: Annotated[bool, Field(alias="isFollowing")]
    following_count: Annotated[int, Field(alias="followingCount")]
    followers_count: Annotated[int, Field(alias="followersCount")]
    posts_count: Annotated[int, Field(alias="postsCount")]
    pinned_post_id: Annotated[UUID | None, Field(alias="pinnedPostId")]
    banner: str | None
    wall_access: Annotated[Literal["everyone", "followers", "mutual", "nobody"], Field(alias="wallAccess")]
