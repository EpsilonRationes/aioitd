from datetime import datetime
from typing import Literal, NamedTuple
from uuid import UUID

import httpx

from aioitd.exceptions import ValidationError
from aioitd.fetch import add_bearer, delete, get, post, put
from aioitd.models.base import Comment, datetime_to_itd_format, Monospace, Strike, Underline, Bold, Italic, Spoiler, \
    Link
from aioitd.models.comments import CreateBaseComment, ReplyComment
from aioitd.models.notifications import Notification
from aioitd.models.posts import *


async def get_post(
        client: httpx.AsyncClient,
        access_token: str,
        post_id: UUID,
        domain: str = "xn--d1ah4a.com"
) -> FullPost:
    """Получить пост.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        post_id: UUID поста
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError:
            пост не существует, удалён, владелец поста забанил, пост принадлежит пользователю с is_private=True,
            на которого вы не подписаны
    """
    response = await get(
        client,
        f"https://{domain}/api/posts/{post_id}",
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()['data']
    return FullPost(**data)


async def delete_post(
        client: httpx.AsyncClient,
        access_token: str,
        post_id: UUID,
        domain: str = "xn--d1ah4a.com"
) -> None:
    """Удалить пост.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        post_id: UUID поста
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        ForbiddenError: Нет прав для удаления поста
        NotFoundError: Пост не найден

    """
    await delete(
        client,
        f"https://{domain}/api/posts/{post_id}",
        headers={"authorization": add_bearer(access_token)}
    )


async def restore_post(
        client: httpx.AsyncClient,
        access_token: str,
        post_id: UUID,
        domain: str = "xn--d1ah4a.com"
) -> None:
    """Восстановить пост.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        post_id: UUID поста
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        ForbiddenError: Нет прав для восстановления поста
        NotFoundError: Пост не найден
    """
    await post(
        client,
        f"https://{domain}/api/posts/{post_id}/restore",
        headers={"authorization": add_bearer(access_token)}
    )


async def like_post(
        client: httpx.AsyncClient,
        access_token: str,
        post_id: UUID,
        domain: str = "xn--d1ah4a.com"
) -> int:
    """Лайкнуть пост.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        post_id: UUID поста
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: Пост не найден

    """
    response = await post(
        client,
        f"https://{domain}/api/posts/{post_id}/like",
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()

    return data["likesCount"]


async def delete_like_post(
        client: httpx.AsyncClient,
        access_token: str,
        post_id: UUID,
        domain: str = "xn--d1ah4a.com"
) -> int:
    """Убрать лайк с пост.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        post_id: UUID поста
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: Пост не найден

    """
    response = await delete(
        client,
        f"https://{domain}/api/posts/{post_id}/like",
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()

    return data["likesCount"]


async def view_post(
        client: httpx.AsyncClient,
        access_token: str,
        post_id: UUID,
        domain: str = "xn--d1ah4a.com"
) -> None:
    """Просмотр на пост.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        post_id: UUID поста
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации


    """
    await post(
        client,
        f"https://{domain}/api/posts/{post_id}/view",
        headers={"authorization": add_bearer(access_token)}
    )


async def pin_post(
        client: httpx.AsyncClient,
        access_token: str,
        post_id: UUID | str,
        domain: str = "xn--d1ah4a.com"
) -> bool:
    """Закрепить пост.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        post_id: UUID поста
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: Пост не найден
        ForbiddenError: Можно прикреплять посты только на своей стене

    """
    response = await post(
        client,
        f"https://{domain}/api/posts/{post_id}/pin",
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()
    return data["success"]


async def unpin_post(
        client: httpx.AsyncClient,
        access_token: str,
        post_id: UUID,
        domain: str = "xn--d1ah4a.com"
) -> bool:
    """Открепить пост.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        post_id: UUID поста
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        NotPinedError: Пост не прикреплён

    """
    response = await delete(
        client,
        f"https://{domain}/api/posts/{post_id}/pin",
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()
    return data["success"]


async def get_posts_by_user(
        client: httpx.AsyncClient,
        access_token: str,
        username_or_id: str | UUID,
        cursor: str | None = None,
        limit: int = 20,
        sort: Literal["new", "popular"] = "new",
        domain: str = "xn--d1ah4a.com"
) -> tuple[Pagination, list[UserPost]]:
    """Посты на стене пользователя.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        username_or_id: имя пользователя или его UUID
        cursor: next_cursor на предыдущей странице
        limit: максимальное количество выданных постов
        sort: сортировка
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: пользователь не найден
        ValidationError: 1 <= limit <= 50
        UserBlockedError: пользователь заблокирован

    """

    response = await get(
        client,
        f"https://{domain}/api/posts/user/{username_or_id}",
        params={"sort": sort, "limit": limit} | (
            {} if cursor is None else {"cursor": cursor}),
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()["data"]
    pagination = Pagination(**data["pagination"])
    posts = list(map(UserPost.model_validate, data["posts"]))

    return pagination, posts


async def get_posts_by_user_liked(
        client: httpx.AsyncClient,
        access_token: str,
        username_or_id: str | UUID,
        cursor: str | None = None,
        limit: int = 20,
        domain: str = "xn--d1ah4a.com"
) -> tuple[Pagination, list[LikedPost]]:
    """Посты на которые пользователей поставил лайк.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        username_or_id: имя пользователя или его UUID
        cursor: next_cursor на предыдущей странице
        limit: максимальное количество выданных постов
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: пользователь не найден
        ValidationError: 1 <= limit <= 50
        UserBlockedError: пользователь заблокирован
    """
    response = await get(
        client,
        f"https://{domain}/api/posts/user/{username_or_id}/liked/",
        params={"sort": "new", "limit": limit} | (
            {} if cursor is None else {"cursor": cursor}),
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()["data"]
    pagination = Pagination(**data["pagination"])
    posts = list(map(LikedPost.model_validate, data["posts"]))

    return pagination, posts


async def get_posts_by_user_wall(
        client: httpx.AsyncClient,
        access_token: str,
        username_or_id: str | UUID,
        cursor: None = None,
        limit: int = 20,
        domain: str = "xn--d1ah4a.com"
) -> tuple[Pagination, list[UserPost]]:
    """Посты на стене пользователя, сделанные не пользователем.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        username_or_id: имя пользователя или его UUID
        cursor: next_cursor на предыдущей странице
        limit: максимальное количество выданных постов
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: пользователь не найден
        ValidationError: 1 <= limit <= 50
        UserBlockedError: пользователь заблокирован
    """
    response = await get(
        client,
        f"https://{domain}/api/posts/user/{username_or_id}/wall",
        params={"sort": "new", "limit": limit} | (
            {} if cursor is None else {"cursor": cursor}),
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()["data"]
    pagination = Pagination(**data["pagination"])
    posts = list(map(UserPost.model_validate, data["posts"]))

    return pagination, posts


async def get_post_comments(
        client: httpx.AsyncClient,
        access_token: str,
        post_id: UUID,
        cursor: str | None = None,
        sort: Literal["popular", "newest", "oldest"] = "popular",
        limit: int = 20,
        domain: str = "xn--d1ah4a.com"
) -> tuple[CommentPagination, list[Comment]]:
    """Получить комментарии под постом.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        post_id: UUID поста
        cursor: next_cursor с предыдущей страницы
        sort: сортировать по
        limit: максимальное количество комментариев на странице
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: Пост не найден
        ParamsValidationError: 1 <= limit <= 500
    """
    response = await get(
        client,
        f"https://{domain}/api/posts/{post_id}/comments",
        params={"sort": sort, "limit": limit} | ({} if cursor is None else {"cursor": cursor}),
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()["data"]
    pagination = CommentPagination(total=data["total"], nextCursor=data["nextCursor"], hasMore=data["hasMore"])
    posts = list(map(Comment.model_validate, data["comments"]))

    return pagination, posts


async def vote(
        client: httpx.AsyncClient,
        access_token: str,
        post_id: UUID,
        options_ids: list[UUID],
        domain: str = "xn--d1ah4a.com"
) -> Poll:
    """Проголосовать в опросе

    Args:
        client: httpx.AsyncClient
        access_token: access токен
        post_id: UUID поста
        options_ids: список UUID выбранных вариантов
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: пост не найден
        ValidationError: Один или несколько вариантов не принадлежат этому опросу
        ValidationError: В этом опросе можно выбрать только один вариант
        ValidationError: len(option_ids) > 0

    """
    response = await post(
        client,
        f"https://{domain}/api/posts/{post_id}/poll/vote",
        json={"optionIds": list(map(str, options_ids))},
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()

    return Poll(**data)


async def create_post(
        client: httpx.AsyncClient,
        access_token: str,
        content: str = '',
        attachment_ids: list[UUID] | None = None,
        wall_recipient_id: UUID = None,
        multiple_choice: bool = False,
        question: str | None = None,
        options: list[str] | None = None,
        spans: list[Monospace | Strike | Underline | Bold | Italic | Spoiler | Link] = None,
        domain: str = "xn--d1ah4a.com"
) -> UserPostWithoutAuthorId:
    """Создать пост.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        content: Текст поста
        attachment_ids: Прикреплённые файлы
        wall_recipient_id: id пользователя
        multiple_choice: возможен ли множественный выбор в опросе
        question: заголовок опроса
        options: варианты ответов
        spans: форматирование текста
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        ValidationError: Нельзя создать пост content="", attachment_ids = [], question = None
        ParamsValidationError: len(content) <= 1_000
        VideoRequiresVerificationError: Загрузка видео доступна только верифицированным пользователям
        ValidationError: len(attachments_ids) <= 10
        ForbiddenError: Некоторые файлы из attachment_ids не существуют
        ParamsValidationError: len(spans) <= 100
        ValidationError: 1 <= len(question) <= 128
        ValidationError: 2 <= len(options) <= 10
        ValidationError: 1 <= len(options[i]) <= 32
    """
    if attachment_ids is None:
        attachment_ids = []

    if options is None:
        options = []

    json = {
        "content": content,
        "attachmentIds": list(map(str, attachment_ids))
    }
    if wall_recipient_id is not None:
        json["wallRecipientId"] = str(wall_recipient_id)

    if question is not None:
        poll = {
            'question': question,
            'multipleChoice': multiple_choice,
            'options': []
        }
        for option in options:
            poll["options"].append({"text": option})
        json['poll'] = poll

    if spans is not None:
        json['spans'] = [span.model_dump() for span in spans]

    response = await post(
        client,
        f"https://{domain}/api/posts",
        json=json,
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()
    for attachment in data['attachments']:
        if attachment['type'] == 'audio':
            del attachment['duration']

    return UserPostWithoutAuthorId(**data)


async def update_post(
        client: httpx.AsyncClient,
        access_token: str,
        post_id: UUID,
        content: str,
        domain: str = "xn--d1ah4a.com"
) -> UpdatePostResponse:
    """Изменить пост
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        post_id: UUID поста
        content: Новый текст поста
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: Пост не найден
        ValidationError: 1 <= len(content) <= 1_000
        ForbiddenError: Нет прав для редактирования этого поста
    """

    response = await put(
        client,
        f"https://{domain}/api/posts/{post_id}",
        json={"content": content},
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()

    return UpdatePostResponse(**data)


async def repost(
        client: httpx.AsyncClient,
        access_token: str,
        post_id: UUID | str,
        content: str = "",
        domain: str = "xn--d1ah4a.com"
) -> PostWithoutAuthorId:
    """Репост.

    Args:
        client: httpx.AsyncClient
        access_token: access токен
        post_id: UUID поста
        content: текст репоста
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: Пост не найден
        ConflictError: Нельзя репостнуть два раза
        ValidationError: Нельзя репостить свои посты
        ValidationError: len(content) <= 1_000
    """
    response = await post(
        client,
        f"https://{domain}/api/posts/{post_id}/repost",
        json={"content": content},
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()
    return PostWithoutAuthorId(**data)
