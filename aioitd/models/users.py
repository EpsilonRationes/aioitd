from enum import Enum

from aioitd.models.base import Author, BaseAuthor, ITDDatetime, ITDBaseModel, WallRecipient, Pin
from typing import Annotated, Literal
from pydantic import Field
from uuid import UUID


class LastSeen(ITDBaseModel):
    unit: str
    value: int | None = None


class BlockedUser(Author):
    is_blocked_by_me: Annotated[bool, Field(alias="isBlockedByMe")]
    online: bool
    last_seen: Annotated[None | LastSeen, Field(alias="lastSeen")]


class BaseFullUser(Author):
    bio: str | None
    banner: str | None
    created_at: Annotated[ITDDatetime, Field(alias="createdAt")]
    posts_count: Annotated[int, Field(alias="postsCount")]
    wall_access: Annotated[Literal["everyone", "followers", "mutual", "nobody"], Field(alias="wallAccess")]
    following_count: Annotated[int, Field(alias="followingCount")]
    followers_count: Annotated[int, Field(alias="followersCount")]
    likes_visibility: Annotated[str, Field(alias="likesVisibility")]


class FullMe(BaseFullUser):
    is_private: Annotated[bool, Field(alias="isPrivate")]
    wall_access: Annotated[Literal["everyone", "followers", "mutual", "nobody"], Field(alias="wallAccess")]
    is_phone_verified: Annotated[bool, Field(alias="isPhoneVerified")]


class UserBlockMe(Author):
    is_blocked_by_them: Annotated[bool, Field(alias="isBlockedByThem")]
    is_private: Annotated[bool, Field(alias="isPrivate")]
    is_followed_by: Annotated[bool, Field(alias="isFollowedBy")]
    is_following: Annotated[bool, Field(alias="isFollowing")]
    following_count: Annotated[int, Field(alias="followingCount")]
    followers_count: Annotated[int, Field(alias="followersCount")]
    posts_count: Annotated[int, Field(alias="postsCount")]
    pinned_post_id: Annotated[UUID | None, Field(alias="pinnedPostId")]
    banner: str | None
    wall_access: Annotated[Literal["everyone", "followers", "mutual", "nobody"], Field(alias="wallAccess")]
    online: bool
    last_seen: Annotated[None | LastSeen, Field(alias="lastSeen")]


class PrivateUser(Author):
    is_private: Annotated[Literal[True], Field(alias="isPrivate")]
    banner: str | None
    posts_count: Annotated[int, Field(alias="postsCount")]
    wall_access: Annotated[Literal["everyone", "followers", "mutual", "nobody"], Field(alias="wallAccess")]
    following_count: Annotated[int, Field(alias="followingCount")]
    followers_count: Annotated[int, Field(alias="followersCount")]
    wall_access: Annotated[Literal["everyone", "followers", "mutual", "nobody"], Field(alias="wallAccess")]
    is_followed_by: Annotated[bool, Field(alias="isFollowedBy")]
    is_following: Annotated[bool, Field(alias="isFollowing")]
    pinned_post_id: Annotated[UUID | None, Field(alias="pinnedPostId")]
    online: bool
    last_seen: Annotated[None | LastSeen, Field(alias="lastSeen")]


class FullUser(BaseFullUser):
    wall_access: Annotated[Literal["everyone", "followers", "mutual", "nobody"], Field(alias="wallAccess")]
    is_followed_by: Annotated[bool, Field(alias="isFollowedBy")]
    is_following: Annotated[bool, Field(alias="isFollowing")]
    pinned_post_id: Annotated[UUID | None, Field(alias="pinnedPostId")]
    online: bool
    last_seen: Annotated[None | LastSeen, Field(alias="lastSeen")]


class PagePagination(ITDBaseModel):
    total: int
    has_more: Annotated[bool, Field(alias="hasMore")]
    limit: int
    page: int


class FollowUser(WallRecipient):
    verified: bool
    is_following: Annotated[bool, Field(alias="isFollowing")]


class Clan(ITDBaseModel):
    avatar: str
    member_count: Annotated[int, Field(alias="memberCount")]


class PinWithDate(Pin):
    granted_at: Annotated[ITDDatetime, Field(alias="grantedAt")]


class Visibility(str, Enum):
    EVERYONE = "everyone"
    FOLLOWERS = "followers"
    MUTUAL = "mutual"
    NOBODY = 'nobody'

    def __str__(self):
        return self.value()


class Privacy(ITDBaseModel):
    is_private: Annotated[bool, Field(alias="isPrivate")]
    likes_visibility: Annotated[Visibility, Field(alias='likesVisibility')]
    wall_access: Annotated[Visibility, Field(alias='wallAccess')]
    show_last_seen: Annotated[bool, Field(alias="showLastSeen")]


class UserWithRole(WallRecipient):
    verified: bool
    is_phone_verified: Annotated[bool, Field(alias="isPhoneVerified")]
    roles: list[str | Literal["user"]]
    bio: str | None


class Profile(ITDBaseModel):
    authenticated: bool
    banned: bool
    user: UserWithRole


class BlockedAuthor(WallRecipient):
    verified: bool
    blocked_at: Annotated[ITDDatetime, Field(alias="blockedAt")]


class Me(BaseAuthor):
    bio: str | None
    update_at: Annotated[ITDDatetime, Field(alias="updatedAt")]
