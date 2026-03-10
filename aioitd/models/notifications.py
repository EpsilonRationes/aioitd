from typing import Annotated, Literal
from uuid import UUID
from enum import Enum

from pydantic import Field

from aioitd.models.base import ITDBaseModel, ITDDatetime
from aioitd.models.users import UserWithAvatar


class NotificationType(str, Enum):
    REPLY = 'reply'
    LIKE = 'like'
    WALL_POST = 'wall_post'
    FOLLOW = 'follow'
    COMMENT = 'comment'
    REPOST = 'repost'
    MENTION = 'mention'

    def __str__(self):
        return self.value


class Actor(UserWithAvatar):
    is_followed_by: Annotated[bool, Field(alias="isFollowedBy")]
    is_following: Annotated[bool, Field(alias="isFollowing")]


class Notification(ITDBaseModel):
    id: UUID
    created_at: Annotated[ITDDatetime, Field(alias="createdAt")]
    preview: str | None
    read: bool
    actor: Actor
    read_at: Annotated[ITDDatetime | None, Field(alias="readAt")]
    target_id: Annotated[UUID | None, Field(alias="targetId")]
    target_type: Annotated[Literal['post'] | None, Field(alias="targetType")]
    type: NotificationType


class NotificationsSettings(ITDBaseModel):
    comments: bool
    enabled: bool
    follows: bool
    mentions: bool
    sound: bool
    likes: bool
    wall_posts: Annotated[bool, Field(alias="wallPosts")]


__all__ = ['NotificationType', 'Actor', 'Notification', 'NotificationsSettings']
