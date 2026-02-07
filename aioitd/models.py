from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal
from uuid import UUID


@dataclass
class Pagination:
    """Пагинация.

    Attributes:
        has_more: есть ли следующая страница
        limit: максимальное количество постов на одной странице
    """
    has_more: bool
    limit: int

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Pagination:
        return Pagination(
            has_more=data["hasMore"],
            limit=data["limit"]
        )


@dataclass
class File:
    """Файл ИТД.

    Attributes:
        id: UUID файла
        filename: имя файла
        url: адрес файла
        mime_type: mime тип (https://developer.mozilla.org/ru/docs/Web/HTTP/Guides/MIME_types)
        size: размер файла в байтах
        created_at: время загрузки
    """
    id: UUID
    filename: str
    url: str
    mime_type: str
    size: int
    created_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> File:
        return File(
            id=UUID(data['id']),
            filename=data['filename'],
            url=data['url'],
            mime_type=data['mimeType'],
            size=data['size'],
            created_at=datetime.fromisoformat(data['createdAt'].replace('Z', '+00:00')) if data.get('createdAt')
            else datetime.now()
        )


@dataclass
class HashTag:
    """Хештег.

    Attributes:
        id: UUID хештега
        name: текст хештега
        posts_count: количество хештегов
    """
    id: UUID
    name: str
    posts_count: int

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> HashTag:
        return HashTag(
            id=UUID(data["id"]),
            name=data["name"],
            posts_count=data["postsCount"]
        )


@dataclass
class UUIDPagination(Pagination):
    """Пагинация постов при поиске по хештегу

    Attributes:
        next_cursor: UUID последнего поста на странице
    """
    next_cursor: UUID

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> UUIDPagination:
        pagination = super().from_json(data)
        return UUIDPagination(
            **pagination.__dict__,
            next_cursor=UUID(data["nextCursor"])
        )


@dataclass
class IntPagination(Pagination):
    next_cursor: int | None

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> IntPagination:
        return IntPagination(
            **(super().from_json(data)).__dict__,
            next_cursor=int(data["nextCursor"]) if data.get("nextCursor") is not None else None
        )


@dataclass
class TimePagination(Pagination):
    next_cursor: datetime | None

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> TimePagination:
        return TimePagination(
            **(super().from_json(data)).__dict__,
            next_cursor=datetime.fromisoformat(data['nextCursor'].replace('Z', '+00:00'))
            if data.get("nextCursor") is not None else None
        )


@dataclass
class CommentPagination:
    has_more: bool
    next_cursor: int | None
    total: int

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> CommentPagination:
        return CommentPagination(
            has_more=data["hasMore"],
            next_cursor=data["nextCursor"],
            total=int(data["total"])
        )


@dataclass
class Attachment:
    id: UUID
    type: str
    url: str
    thumbnail_url: None | str
    width: int | None
    height: int | None

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Attachment:
        return Attachment(
            id=UUID(data["id"]),
            type=data["type"],
            url=data["url"],
            thumbnail_url=data["thumbnailUrl"],
            width=data["width"],
            height=data["height"],
        )


@dataclass
class BaseAuthor:
    id: UUID
    username: str
    display_name: str

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> BaseAuthor:
        return BaseAuthor(
            id=UUID(data["id"]),
            username=data["username"],
            display_name=data["displayName"]
        )


@dataclass
class WallRecipient(BaseAuthor):
    avatar: str

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> WallRecipient:
        return WallRecipient(
            **(super().from_json(data)).__dict__,
            avatar=data["avatar"],
        )


@dataclass
class Pin:
    slug: str
    name: str
    description: str

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Pin:
        return Pin(
            slug=data['slug'],
            name=data['name'],
            description=data["description"]
        )

@dataclass
class PinWithDate(Pin):
    granted_at: datetime

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> PinWithDate:
        return PinWithDate(
            **(super().from_json(data)).__dict__,
            granted_at=datetime.fromisoformat(data['grantedAt'].replace('Z', '+00:00'))
        )


@dataclass
class Author(WallRecipient):
    verified: bool
    pin: None | Pin

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Author:
        return Author(
            **(super().from_json(data)).__dict__,
            verified=data["verified"],
            pin=Pin.from_json(data["pin"]) if data['pin'] is not None else None
        )


@dataclass
class User(Author):
    followers_count: int

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> User:
        return User(
            **(super().from_json(data)).__dict__,
            followers_count=data["followersCount"],
        )


@dataclass
class Me(BaseAuthor):
    bio: str
    update_at: datetime

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Me:
        return Me(
            **(super().from_json(data)).__dict__,
            bio=data["bio"],
            update_at=datetime.fromisoformat(data['updatedAt'].replace('Z', '+00:00'))
        )


@dataclass
class FullUser(User):
    bio: str
    banner: str | None
    created_at: datetime
    is_followed_by: bool
    is_following: bool
    pinned_post_id: UUID | None
    posts_count: int
    wall_closed: bool

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> FullUser:
        return FullUser(
            **(super().from_json(data)).__dict__,
            bio=data["bio"],
            created_at=datetime.fromisoformat(data['createdAt'].replace('Z', '+00:00')),
            banner=data.get("banner"),
            is_following=data["isFollowing"],
            is_followed_by=data["isFollowedBy"],
            pinned_post_id=UUID(data["pinnedPostId"]) if data.get("pinnedPostId") is not None else None,
            posts_count=data["postsCount"],
            wall_closed=data["wallClosed"]
        )

@dataclass
class FollowUser(Author):
    is_following: bool

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> FollowUser:
        return FollowUser(
            **(super().from_json(data)).__dict__,
            is_following=data["isFollowing"]
        )


@dataclass
class BasePost:
    id: UUID
    content: str
    author: Author
    likes_count: int
    comments_count: int
    reposts_count: int
    views_count: int
    created_at: datetime
    attachments: list[Attachment]

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> BasePost:
        return BasePost(
            id=UUID(data["id"]),
            content=data["content"],
            author=Author.from_json(data["author"]),
            likes_count=data["likesCount"],
            comments_count=data["commentsCount"],
            reposts_count=data["repostsCount"],
            views_count=data["viewsCount"],
            created_at=datetime.fromisoformat(data['createdAt'].replace('Z', '+00:00')),
            attachments=list(map(Attachment.from_json, data["attachments"]))
        )


@dataclass
class OriginalPost(BasePost):
    is_deleted: bool

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> OriginalPost:
        return OriginalPost(
            **(super().from_json(data)).__dict__,
            is_deleted=data["isDeleted"]
        )


@dataclass
class Post(BasePost):
    is_liked: bool
    is_reposted: bool
    is_owner: bool
    is_viewed: bool

    original_post: OriginalPost | None
    wall_recipient_id: UUID | None
    wall_recipient: WallRecipient | None

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Post:
        return Post(
            **(super().from_json(data)).__dict__,
            is_liked=data["isLiked"],
            is_reposted=data["isReposted"],
            is_owner=data["isOwner"],
            is_viewed=data.get("isViewed", False),
            original_post=OriginalPost.from_json(data["originalPost"]) if data.get("originalPost") else None,
            wall_recipient_id=UUID(data["walRecipientId"]) if data.get("walRecipientId") else None,
            wall_recipient=WallRecipient.from_json(data["walRecipient"]) if data.get("walRecipient") else None
        )


@dataclass
class Comment:
    id: UUID
    created_at: datetime
    content: str
    attachments: list[CommentAttachment]
    is_liked: bool
    replies_count: int
    replies: list[Replay]
    likes_count: int
    author: Author

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Comment:
        return Comment(
            id=UUID(data["id"]),
            created_at=datetime.fromisoformat(data['createdAt'].replace('Z', '+00:00')),
            content=data["content"],
            attachments=list(map(CommentAttachment.from_json, data["attachments"])),
            is_liked=data["isLiked"],
            replies_count=data["repliesCount"],
            likes_count=data["likesCount"],
            author=Author.from_json(data["author"]),
            replies=list(map(Replay.from_json, data.get("replies", [])))
        )


@dataclass
class Replay(Comment):
    replay_to: BaseAuthor

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Replay:
        return Replay(
            **(super().from_json(data)).__dict__,
            replay_to=BaseAuthor.from_json(data["replyTo"])
        )


@dataclass
class CommentAttachment(Attachment):
    duration: int | None
    order: int

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> CommentAttachment:
        return CommentAttachment(
            **(super().from_json(data)).__dict__,
            duration=data["duration"],
            order=data["order"]
        )


@dataclass
class FullPost(Post):
    comments: list[Comment]

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> FullPost:
        return FullPost(
            **(super().from_json(data)).__dict__,
            comments=list(map(Comment.from_json, data["comments"]))
        )


@dataclass
class Report:
    id: UUID
    created_at: datetime

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Report:
        return Report(
            id=UUID(data["id"]),
            created_at=datetime.fromisoformat(data['createdAt'].replace('Z', '+00:00'))
        )


@dataclass
class Privacy:
    is_private: bool
    wall_closed: bool

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Privacy:
        return Privacy(
            is_private=data["isPrivate"],
            wall_closed=data["wallClosed"]
        )


@dataclass
class Clan:
    avatar: str
    member_count: int

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Clan:
        return Clan(
            avatar=data["avatar"],
            member_count=data["memberCount"]
        )

@dataclass
class Notification:
    id: UUID
    created_at: datetime
    preview: str
    read: bool
    read_at: datetime | None
    target_id: UUID | None
    target_type: Literal['reply', 'like', 'wall_post', 'follow', 'comment']

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Notification:
        return Notification(
            id=UUID(data["id"]),
            created_at=datetime.fromisoformat(data["createdAt"].replace('Z', '+00:00')),
            preview=data["preview"],
            read=data["read"],
            read_at=datetime.fromisoformat(data["readAt"].replace('Z', '+00:00')) if data.get("readAt") else None,
            target_id=UUID(data["targetId"]) if data["targetId"] is not None else None,
            target_type=data["targetType"]
        )
