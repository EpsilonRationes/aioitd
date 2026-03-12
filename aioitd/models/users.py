from enum import Enum

from aioitd.models.base import ITDDatetime, ITDBaseModel
from typing import Annotated, Literal
from pydantic import Field
from uuid import UUID


class Visibility(str, Enum):
    EVERYONE = "everyone"
    FOLLOWERS = "followers"
    MUTUAL = "mutual"
    NOBODY = 'nobody'

    def __str__(self):
        return self.value


class Privacy(ITDBaseModel):
    is_private: Annotated[bool, Field(alias="isPrivate")]
    likes_visibility: Annotated[Visibility, Field(alias='likesVisibility')]
    wall_access: Annotated[Visibility, Field(alias='wallAccess')]
    show_last_seen: Annotated[bool, Field(alias="showLastSeen")]


class Profile(ITDBaseModel):
    authenticated: bool
    banned: bool
    user: UserWithRoles | None
    """None если отправить запрос без access_token"""


class LastSeenUnit(str, Enum):
    JUST_NOW = 'just_now'
    MINUTES = 'minutes'
    HOURS = 'hours'
    RECENTLY = 'recently'
    THIS_WEEK = 'this_week'
    THIS_MONTH = 'this_month'
    LONG_AGO = 'long_ago'


class LastSeen(ITDBaseModel):
    unit: LastSeenUnit
    value: int | None = None


class Clan(ITDBaseModel):
    avatar: str
    member_count: Annotated[int, Field(alias="memberCount")]


class PinSlug(str, Enum):
    KIRILL67_202602_INFECTED = "kirill67_202602_infected"
    KIRILL67_202602_SURVIVOR = "kirill67_202602_survivor"

    def __str__(self):
        return self.value


class Pin(ITDBaseModel):
    description: str
    name: str
    slug: PinSlug


class PinWithDate(Pin):
    granted_at: Annotated[ITDDatetime, Field(alias="grantedAt")]


class UserStab(ITDBaseModel):
    id: UUID
    username: str | None
    display_name: Annotated[str, Field(alias="displayName")]


class UserWithAvatar(UserStab):
    avatar: str


class UserWithVerified(UserWithAvatar):
    verified: bool


class UserWithFollowersCount(UserWithVerified):
    followers_count: Annotated[int, Field(alias="followersCount")]


class UserWithPin(UserWithVerified):
    pin: Pin | None


class UserWithRoles(UserWithVerified):
    is_phone_verified: Annotated[bool, Field(alias="isPhoneVerified")]
    roles: list[str | Literal["user"]]
    bio: str | None


class UserWithFollowing(UserWithVerified):
    is_following: Annotated[bool, Field(alias="isFollowing")]


class BlockedAuthor(UserWithVerified):
    blocked_at: Annotated[ITDDatetime, Field(alias="blockedAt")]


class Me(UserStab):
    bio: str | None
    update_at: Annotated[ITDDatetime, Field(alias="updatedAt")]


class UserBlockedByMe(UserWithPin):
    is_blocked_by_me: Annotated[bool, Field(alias="isBlockedByMe")]
    last_seen: Annotated[None | LastSeen, Field(alias="lastSeen")]
    online: bool


class User(UserWithPin):
    wall_access: Annotated[Visibility, Field(alias="wallAccess")]
    banner: str | None
    is_followed_by: Annotated[bool, Field(alias="isFollowedBy")]
    is_following: Annotated[bool, Field(alias="isFollowing")]
    posts_count: Annotated[int, Field(alias="postsCount")]
    following_count: Annotated[int, Field(alias="followingCount")]
    followers_count: Annotated[int, Field(alias="followersCount")]


class BaseFullUser(User):
    bio: str | None
    created_at: Annotated[ITDDatetime, Field(alias="createdAt")]
    likes_visibility: Annotated[str, Field(alias="likesVisibility")]


class FullMe(BaseFullUser):
    is_private: Annotated[bool, Field(alias="isPrivate")]
    is_phone_verified: Annotated[bool, Field(alias="isPhoneVerified")]


class LastSeenMixin(User):
    pinned_post_id: Annotated[UUID | None, Field(alias="pinnedPostId")]
    last_seen: Annotated[None | LastSeen, Field(alias="lastSeen")]
    online: bool


class FullUser(BaseFullUser, LastSeenMixin): ...


class UserBlockMe(LastSeenMixin):
    is_private: Annotated[bool, Field(alias="isPrivate")]
    is_blocked_by_them: Annotated[bool, Field(alias="isBlockedByThem")]


class PrivateUser(LastSeenMixin):
    is_private: Annotated[bool, Field(alias="isPrivate")]


class DeletedMe(ITDBaseModel):
    can_restore: Annotated[bool, Field(alias="canRestore")]
    is_deleted: Annotated[bool, Field(alias='isDeleted')]
    restore_deadline: Annotated[ITDDatetime, Field(alias="restoreDeadline")]


__all__ = [
    'BaseFullUser', 'BlockedAuthor', 'Clan', 'FullMe', 'FullUser', 'LastSeen', 'LastSeenMixin', 'Me', 'Pin', 'PinSlug',
    'PinWithDate', 'Privacy', 'PrivateUser', 'Profile', 'User', 'UserBlockedByMe', 'UserBlockMe', 'UserStab',
    'UserWithAvatar', 'UserWithFollowersCount', 'UserWithFollowing', 'UserWithPin', 'UserWithRoles', 'UserWithVerified',
    'Visibility', 'LastSeenUnit', 'DeletedMe'
]
