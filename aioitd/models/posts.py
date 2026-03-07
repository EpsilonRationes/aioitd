from aioitd.models.base import Author, Comment, ITDDatetime, ITDBaseModel, ImagePostAttachment, \
    AudioOrVideoPostAttachment, \
    OriginalPost, Pin, Span, WallRecipient, ImagePostAttachmentWithoutFileName, \
    AudioOrVideoPostAttachmentWithoutFileName
from uuid import UUID
from pydantic import Field
from typing import Annotated


class Option(ITDBaseModel):
    id: UUID
    position: int
    text: str
    votest_count: Annotated[int, Field(alias="votesCount")]


class Poll(ITDBaseModel):
    created_at: Annotated[ITDDatetime, Field(alias="createdAt")]
    has_voted: Annotated[bool, Field(alias="hasVoted")]
    id: UUID
    multiple_choice: Annotated[bool, Field(alias="multipleChoice")]
    post_id: Annotated[UUID, Field(alias="postId")]
    question: str
    total_votes: Annotated[int, Field(alias="totalVotes")]
    voted_option_ids: Annotated[list[UUID], Field(alias="votedOptionIds")]
    options: list[Option]


class Counts(ITDBaseModel):
    comments_count: Annotated[int, Field(alias="commentsCount")]
    respot_count: Annotated[int, Field(alias="repostsCount")]
    views_count: Annotated[int, Field(alias="viewsCount")]
    spans: list[Span]


class UpdatePostResponse(ITDBaseModel):
    id: UUID
    content: str
    spans: list[Span]
    updated_at: Annotated[ITDDatetime | None, Field(alias="updatedAt")]


class BasePostWithoutAuthorId(ITDBaseModel):
    id: UUID
    content: Annotated[str, Field(max_length=5000)]
    author: AuthorWithoutId
    attachments: list[Annotated[ImagePostAttachment | AudioOrVideoPostAttachment, Field(discriminator="type")]]
    likes_count: Annotated[int, Field(alias="likesCount")]
    created_at: Annotated[ITDDatetime, Field(alias="createdAt")]


class UserPostWithoutAuthorId(BasePostWithoutAuthorId, Counts):
    is_liked: Annotated[bool, Field(alias="isLiked")]

    wall_recipient_id: Annotated[None | UUID, Field(alias="wallRecipientId")]

    is_reposted: Annotated[bool, Field(alias="isReposted")]

    is_owner: Annotated[bool, Field(alias="isOwner")]

    wall_recipient: Annotated[None | WallRecipient, Field(alias="wallRecipient")]

    poll: Poll | None




class AuthorWithoutId(ITDBaseModel):
    avatar: str
    pin: Pin | None
    verified: bool
    username: str | None
    display_name: Annotated[str, Field(alias="displayName")]


class CommentPagination(ITDBaseModel):
    total: int
    has_more: Annotated[bool, Field(alias="hasMore")]
    next_cursor: Annotated[str | None, Field(alias="nextCursor")]


class BasePostWithoutAttachmentsFileName(ITDBaseModel):
    id: UUID
    content: Annotated[str, Field(max_length=5000)]
    author: Author
    attachments: list[Annotated[ImagePostAttachmentWithoutFileName | AudioOrVideoPostAttachmentWithoutFileName, Field(discriminator="type")]]
    likes_count: Annotated[int, Field(alias="likesCount")]
    created_at: Annotated[ITDDatetime, Field(alias="createdAt")]

class BasePost(ITDBaseModel):
    id: UUID
    content: Annotated[str, Field(max_length=5000)]
    author: Author
    attachments: list[Annotated[ImagePostAttachment | AudioOrVideoPostAttachment, Field(discriminator="type")]]
    likes_count: Annotated[int, Field(alias="likesCount")]
    created_at: Annotated[ITDDatetime, Field(alias="createdAt")]


class AuthorWithOnline(Author):
    online: bool


class Post(BasePost, Counts):
    is_liked: Annotated[bool, Field(alias="isLiked")]
    is_viewed: Annotated[bool, Field(alias="isViewed")]
    author: AuthorWithOnline
    poll: Poll | None

    wall_recipient_id: Annotated[None | UUID, Field(alias="wallRecipientId")]

    is_reposted: Annotated[bool, Field(alias="isReposted")]
    original_post: Annotated[OriginalPost | None, Field(alias="originalPost")]

    is_owner: Annotated[bool, Field(alias="isOwner")]


class IntCommentPagination(CommentPagination):
    next_cursor: Annotated[int | None, Field(alias="nextCursor")]


class UUIDCommentPagination(CommentPagination):
    next_cursor: Annotated[UUID | None, Field(alias="nextCursor")]


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


class UserPost(Post):
    author: Author
    #attachments: list[Annotated[ImagePostAttachmentWithoutFileName | AudioOrVideoPostAttachmentWithoutFileName, Field(discriminator="type")]]
    wall_recipient: Annotated[None | WallRecipient, Field(alias="wallRecipient")]
    dominant_emoji: Annotated[str | None, Field(alias="dominantEmoji")]
    edited_at: Annotated[ITDDatetime | None, Field(alias="editedAt")]


class LikedPost(Post):
    author: Author
    dominant_emoji: Annotated[str | None, Field(alias="dominantEmoji")]
    edited_at: Annotated[ITDDatetime | None, Field(alias="editedAt")]

class PostWithoutAuthorId(BasePostWithoutAuthorId, Counts):
    is_liked: Annotated[bool, Field(alias="isLiked")]

    wall_recipient_id: Annotated[None | UUID, Field(alias="wallRecipientId")]

    is_reposted: Annotated[bool, Field(alias="isReposted")]
    original_post: Annotated[OriginalPost | None, Field(alias="originalPost")]

    is_owner: Annotated[bool, Field(alias="isOwner")]


class FullPost(UserPost):
    author: Author
    attachments: list[Annotated[ImagePostAttachmentWithoutFileName | AudioOrVideoPostAttachmentWithoutFileName, Field(discriminator="type")]]
    comments: list[Comment]
    dominant_emoji: Annotated[str | None, Field(alias="dominantEmoji")]
    edited_at: Annotated[ITDDatetime | None, Field(alias="editedAt")]
