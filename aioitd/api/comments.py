from uuid import UUID

import httpx

from aioitd.fetch import add_bearer, delete, get, post, put, patch
from aioitd.models.comments import CreateBaseComment, ReplyComment, UpdateCommentResponse


async def comment(
        client: httpx.AsyncClient,
        access_token: str,
        post_id: UUID,
        content: str = "",
        attachment_ids: list[UUID] | None = None,
        domain: str = "xn--d1ah4a.com"
) -> CreateBaseComment:
    """
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        post_id: UUID поста
        content: текст поста
        attachment_ids: список UUID файлов
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: пост не найден
        ITDError: attachments_ids[i] файла с таким UUID не существует
        ValidationError: Нельзя создать комментарий content="", attachment_ids = []
        ParamsValidationError: len(attachments_ids) <= 4
        ITDError: не должно быть одинаковых attachment_ids[i]
        ParamsValidationError: len(content) <= 1_000
        RateLimitError: ограничение комментариев за время
    """
    if attachment_ids is None:
        attachment_ids = []

    response = await post(
        client,
        f"https://{domain}/api/posts/{post_id}/comments",
        json={"content": content, "attachmentIds": list(map(str, attachment_ids))},
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()
    return CreateBaseComment(**data)


async def replies(
        client: httpx.AsyncClient,
        access_token: str,
        comment_id: UUID,
        content: str = "",
        replay_to_user_id: UUID = None,
        attachment_ids: list[UUID] = None,
        domain: str = "xn--d1ah4a.com"
) -> ReplyComment:
    """Ответить на комментарий

    Args:
        client: httpx.AsyncClient
        access_token: access токен
        comment_id: UUID комментария
        content: текст комментария
        replay_to_user_id: UUID пользователя, которому ответ
        attachment_ids: список UUID файлов
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: комментарий не найден
        ValidationError: Нельзя создать ответ content="", attachment_ids = []
        ITDError: attachments_ids[i] файла с таким UUID не существует
        ParamsValidationError: len(attachments_ids) <= 4
        ParamsValidationError: len(content) <= 1_000
        RateLimitError: ограничение ответов на комментарии за время
    """
    if attachment_ids is None:
        attachment_ids = []

    response = await post(
        client,
        f"https://{domain}/api/comments/{comment_id}/replies",
        json={"content": content, "attachmentIds": list(map(str, attachment_ids))}
             | ({} if replay_to_user_id is None else {"replayToUserId": str(replay_to_user_id)}),
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()
    return ReplyComment(**data)


async def edit_comment(
        client: httpx.AsyncClient,
        access_token: str,
        comment_id: UUID,
        content: str,
        domain: str = "xn--d1ah4a.com"
) -> UpdateCommentResponse:
    """Ответить на комментарий.

    Args:
        client: httpx.AsyncClient
        access_token: access токен
        comment_id: UUID комментария
        content: текст комментария
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: комментарий не найден
        ForbiddenError: нет прав на редактирование этого комментария
        ParamsValidationError: 1 <= len(content) <= 1_000
    """

    response = await patch(
        client,
        f"https://{domain}/api/comments/{comment_id}",
        json={"content": content},
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()
    return UpdateCommentResponse(**data)


async def delete_comment(
        client: httpx.AsyncClient,
        access_token: str,
        comment_id: UUID,
        domain: str = "xn--d1ah4a.com"
) -> None:
    """Удалить комментарий.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        comment_id: UUID комментария
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: комментарий не найден
        ForbiddenError: нет прав на удаление комментария
    """
    await delete(
        client,
        f"https://{domain}/api/comments/{comment_id}",
        headers={"authorization": add_bearer(access_token)}
    )


async def restore_comment(
        client: httpx.AsyncClient,
        access_token: str,
        comment_id: UUID,
        domain: str = "xn--d1ah4a.com"
) -> None:
    """Восстановить комментарий.

    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        comment_id: UUID комментария
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: комментарий не найден
        ForbiddenError: нет прав на восстановление комментария
    """
    await post(
        client,
        f"https://{domain}/api/comments/{comment_id}/restore",
        headers={"authorization": add_bearer(access_token)}
    )


async def like_comment(
        client: httpx.AsyncClient,
        access_token: str,
        comment_id: UUID,
        domain: str = "xn--d1ah4a.com"
) -> str:
    """Поставить лайк на комментарий.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        comment_id: UUID комментария
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: комментарий не найден
    """
    response = await post(
        client,
        f"https://{domain}/api/comments/{comment_id}/like",
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()
    return data["likesCount"]


async def delete_like_comment(
        client: httpx.AsyncClient,
        access_token: str,
        comment_id: UUID,
        domain: str = "xn--d1ah4a.com"
) -> str:
    """Удалить лайк с комментария.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        comment_id: UUID комментария
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: комментарий не найден
    """
    response = await delete(
        client,
        f"https://{domain}/api/comments/{comment_id}/like",
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()
    return data["likesCount"]
