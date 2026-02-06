from dataclasses import dataclass
from datetime import datetime
from json import JSONDecodeError

import httpx
from uuid import UUID
from typing import Literal, Any

from aioitd import UnauthorizedError, UnknowError
from aioitd.api import add_bearer, Pagination


@dataclass
class PopularPostsPagination(Pagination):
    """Пагинация популярных постов"""
    next_cursor: int

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> PopularPostsPagination:
        return PopularPostsPagination(
            **(super().from_json(data)).__dict__,
            next_cursor=int(data["nextCursor"])
        )


@dataclass
class Attachment:
    id: UUID
    type: str
    url: str
    thumbnail_url: None | str
    width: int
    height: int

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
class WallRecipient:
    id: UUID
    avatar: str
    username: str
    display_name: str

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> WallRecipient:
        return WallRecipient(
            id=UUID(data["id"]),
            avatar=data["avatar"],
            username=data["username"],
            display_name=data["displayName"]
        )


@dataclass
class Author(WallRecipient):
    verified: bool

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Author:
        return Author(
            **(super().from_json(data)).__dict__,
            verified=data["verified"],
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
    author_id: UUID

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
            author_id=UUID(data["authorId"]),
            is_liked=data["isLiked"],
            is_reposted=data["isReposted"],
            is_owner=data["isOwner"],
            is_viewed=data["isViewed"],
            original_post=OriginalPost.from_json(data["originalPost"]) if data.get("originalPost") else None,
            wall_recipient_id=UUID(data["walRecipientId"]) if data.get("walRecipientId") else None,
            wall_recipient=WallRecipient.from_json(data["walRecipient"]) if data.get("walRecipient") else None
        )


async def get_popular_posts(
        session: httpx.AsyncClient,
        access_token: str,
        cursor: int | None = None,
        limit: int = 20,
):
    """Получить посты, лента.

    Args:
        session: httpx.AsyncClient
        access_token: access токен
        cursor: Номер страницы
        limit: максимальное количество постов на странице

    Raises:
        UnauthorizedError: неверный access токен
    """
    if not (1 <= limit <= 50):
        raise ValueError("limit должен быть больше от 1 до 50")

    result = await session.get(
        f"https://xn--d1ah4a.com/api/posts?limit={limit}&tab=popular" if cursor is None else
        f"https://xn--d1ah4a.com/api/posts?limit={limit}&tab=popular&cursor={cursor}",
        headers={"authorization": add_bearer(access_token)}
    )

    if result.text == "UNAUTHORIZED":
        raise UnauthorizedError

    response = result.json()
    if 'error' in response:
        raise UnknowError(code=response['error']['code'], message=response['error']['message'])

    pagination = response["data"]["pagination"]
    pagination = PopularPostsPagination.from_json(pagination)

    posts = list(map(Post.from_json, response["data"]["posts"]))

    print(result.text)

    return pagination, posts
