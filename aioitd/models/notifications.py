from typing import Annotated, Literal
from uuid import UUID
from enum import Enum

from pydantic import Field

from aioitd.models.base import ITDBaseModel, ITDDatetime


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


class Actor(ITDBaseModel):
    id: UUID
    username: str | None
    display_name: Annotated[str, Field(alias="displayName")]
    avatar: str
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
