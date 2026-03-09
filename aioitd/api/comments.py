from uuid import UUID

import httpx

from aioitd.fetch import add_bearer, delete, post, patch
from aioitd.models.comments import Reply, Comment, UpdateCommentResponse


async def comment(
        client: httpx.AsyncClient,
        access_token: str,
        post_id: UUID,
        content: str = "",
        attachment_ids: list[UUID] | None = None,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> Comment:
    """Создать комментарий.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        post_id: UUID поста
        content: текст поста
        attachment_ids: список UUID файлов
        domain: домен

    Returns:
        Созданный комментарий

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: пост не найден
        ITDError: attachments_ids[i] файла с таким UUID не существует
        ValidationError: Нельзя создать комментарий content="", attachment_ids = []
        ParamsValidationError: len(attachments_ids) <= 4
        ITDError: не должно быть одинаковых attachment_ids[i]
        ParamsValidationError: len(content) <= 1_000

    Examples:
        ```python
        from httpx import AsyncClient
        from aioitd.api import refresh, get_posts, comment, upload_file

        refresh_token = "ВАШ ТОКЕН"

        async def main():
            async with AsyncClient() as client:
                access_token = await refresh(client, refresh_token)
                _, posts = await get_posts(client, access_token)
                with open('tests/image.jpg', 'rb') as f:
                    image = await upload_file(client, access_token, f)
                await comment(client, access_token, posts[0].id, "Это комментарий", [image.id])
        ```
    """
    if attachment_ids is None:
        attachment_ids = []

    response = await post(
        client,
        f"https://{domain}/api/posts/{post_id}/comments",
        json={"content": content, "attachmentIds": list(map(str, attachment_ids))},
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()
    data['replies'] = []
    return Comment(**data)


async def replies(
        client: httpx.AsyncClient,
        access_token: str,
        comment_id: UUID,
        content: str = "",
        replay_to_user_id: UUID = None,
        attachment_ids: list[UUID] = None,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> Reply:
    """Ответить на комментарий

    Args:
        client: httpx.AsyncClient
        access_token: access токен
        comment_id: UUID комментария
        content: текст комментария
        replay_to_user_id: UUID пользователя, которому ответ
        attachment_ids: список UUID файлов
        domain: домен

    Returns:
        Созданный ответ

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: комментарий не найден
        ValidationError: Нельзя создать ответ content="", attachment_ids = []
        ITDError: attachments_ids[i] файла с таким UUID не существует
        ParamsValidationError: len(attachments_ids) <= 4
        ParamsValidationError: len(content) <= 1_000

    Examples:
        ```python
        from httpx import AsyncClient
        from aioitd.api import refresh, get_posts, comment, upload_file, replies

        refresh_token = "ВАШ ТОКЕН"

        async def main():
            async with AsyncClient() as client:
                access_token = await refresh(client, refresh_token)
                _, posts = await get_posts(client, access_token)
                with open('tests/image.jpg', 'rb') as f:
                    image = await upload_file(client, access_token, f)
                comm = await comment(client, access_token, posts[0].id, "Это комментарий")
                await replies(client, access_token, comm.id, 'Это ответ', attachment_ids=[image.id])
        ```
    """
    if attachment_ids is None:
        attachment_ids = []

    response = await post(
        client,
        f"https://{domain}/api/comments/{comment_id}/replies",
        json={"content": content, "attachmentIds": list(map(str, attachment_ids))}
             | ({} if replay_to_user_id is None else {"replayToUserId": str(replay_to_user_id)}),
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()
    data['repliesCount'] = 0
    data['replies'] = []
    return Reply(**data)


async def edit_comment(
        client: httpx.AsyncClient,
        access_token: str,
        comment_id: UUID,
        content: str,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> UpdateCommentResponse:
    """Ответить на комментарий.

    Args:
        client: httpx.AsyncClient
        access_token: access токен
        comment_id: UUID комментария
        content: текст комментария
        domain: домен

    Returns:
        Новое содержимое комментария

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: комментарий не найден
        ForbiddenError: нет прав на редактирование этого комментария
        ParamsValidationError: 1 <= len(content) <= 1_000

    Examples:
        ```python
        from httpx import AsyncClient
        from aioitd.api import refresh, get_posts, comment, edit_comment

        refresh_token = "ВАШ ТОКЕН"

        async def main():
            async with AsyncClient() as client:
                access_token = await refresh(client, refresh_token)
                _, posts = await get_posts(client, access_token)
                comm = await comment(client, access_token, posts[0].id, "Это комментарий")
                await edit_comment(client, access_token, comm.id, 'Изменённый комментарий')
        ```
    """

    response = await patch(
        client,
        f"https://{domain}/api/comments/{comment_id}",
        json={"content": content},
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()
    return UpdateCommentResponse(**data)


async def delete_comment(
        client: httpx.AsyncClient,
        access_token: str,
        comment_id: UUID,
        domain: str = "xn--d1ah4a.com",
        **kwargs
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

    Examples:
        ```python
        from httpx import AsyncClient
        from aioitd.api import refresh, get_posts, comment, delete_comment

        refresh_token = "ВАШ ТОКЕН"

        async def main():
            async with AsyncClient() as client:
                access_token = await refresh(client, refresh_token)
                _, posts = await get_posts(client, access_token)
                comm = await comment(client, access_token, posts[0].id, "Это комментарий")
                await delete_comment(client, access_token, comm.id)
        ```
    """
    await delete(
        client,
        f"https://{domain}/api/comments/{comment_id}",
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )


async def restore_comment(
        client: httpx.AsyncClient,
        access_token: str,
        comment_id: UUID,
        domain: str = "xn--d1ah4a.com",
        **kwargs
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

    Examples:
        ```python
        from httpx import AsyncClient
        from aioitd.api import refresh, get_posts, comment, delete_comment, restore_comment

        refresh_token = "101c68cc5142de4737f3112fb8236715595e6f9ce0ea19ababb219210f526373"

        async def main():
            async with AsyncClient() as client:
                access_token = await refresh(client, refresh_token)
                _, posts = await get_posts(client, access_token)
                comm = await comment(client, access_token, posts[0].id, "Это комментарий")
                await delete_comment(client, access_token, comm.id)
                await restore_comment(client, access_token, comm.id)
        ```
    """
    await post(
        client,
        f"https://{domain}/api/comments/{comment_id}/restore",
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )


async def like_comment(
        client: httpx.AsyncClient,
        access_token: str,
        comment_id: UUID,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> int:
    """Поставить лайк на комментарий.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        comment_id: UUID комментария
        domain: домен

    Returns:
        Лайков на комментарии

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: комментарий не найден

    Examples:
        ```python
        from httpx import AsyncClient
        from aioitd.api import refresh, get_posts_by_user, like_comment, get_post_comments

        refresh_token = "101c68cc5142de4737f3112fb8236715595e6f9ce0ea19ababb219210f526373"

        async def main():
            async with AsyncClient() as client:
                access_token = await refresh(client, refresh_token)
                _, posts = await get_posts_by_user(client, access_token, 'nowkie')
                _, comments = await get_post_comments(client, access_token, posts[0].id)
                await like_comment(client, access_token, comments[0].id)
        ```
    """
    response = await post(
        client,
        f"https://{domain}/api/comments/{comment_id}/like",
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()
    return data["likesCount"]


async def unlike_comment(
        client: httpx.AsyncClient,
        access_token: str,
        comment_id: UUID,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> int:
    """Удалить лайк с комментария.
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        comment_id: UUID комментария
        domain: домен

    Returns:
        Лайков на комментарии

    Raises:
        UnauthorizedError: ошибка авторизации
        NotFoundError: комментарий не найден

    Examples:
        ```python
        from httpx import AsyncClient
        from aioitd.api import refresh, get_posts_by_user, like_comment, get_post_comments, delete_like_comment

        refresh_token = "ВАШ ТОКЕН"

        async def main():
            async with AsyncClient() as client:
                access_token = await refresh(client, refresh_token)
                _, posts = await get_posts_by_user(client, access_token, 'nowkie')
                _, comments = await get_post_comments(client, access_token, posts[0].id)
                await like_comment(client, access_token, comments[0].id)
                await delete_like_comment(client, access_token, comments[0].id)
        ```
    """
    response = await delete(
        client,
        f"https://{domain}/api/comments/{comment_id}/like",
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )
    data = response.json()
    return data["likesCount"]


__all__ = [
    "delete_comment", "like_comment", "unlike_comment", "comment", "edit_comment", "replies", "restore_comment"
]
