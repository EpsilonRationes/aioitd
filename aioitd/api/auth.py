import httpx

from aioitd.fetch import add_bearer, post


async def refresh(
        client: httpx.AsyncClient,
        refresh_token: str,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> str:
    """Получить access_token.

    Args:
        client: httpx.AsyncClient
        refresh_token: refresh токен
        domain: домен

    Returns:
        access токен

    Raises:
        TokenNotFoundError: Такого токена не существует
        TokenRevokedError: Токен отозван
        TokenMissingError: Токен не указан (равен пустой строке)
        TokenExpiredError: Токен истёк

    Examples:
        ```python
        from httpx import AsyncClient
        from aioitd.api import refresh

        refresh_token = "ВАШ ТОКЕН"

        async def main():
            async with AsyncClient() as client:
                access_token = await refresh(client, refresh_token)
                print(access_token)
        ```
    """
    response = await post(
        client,
        f"https://{domain}/api/v1/auth/refresh",
        cookies={"refresh_token": refresh_token},
        **kwargs
    )
    return response.json()["accessToken"]


async def logout(
        client: httpx.AsyncClient,
        refresh_token: str,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> None:
    """Выйти из аккаунта, отозвать токен. Работает при любом токене: просроченном, не существующим, пустой строкой.

    Args:
        client: httpx.AsyncClient
        refresh_token: refresh токен
        domain: домен

    Examples:
        ```python
        from httpx import AsyncClient
        from aioitd.api import logout

        refresh_token = "ВАШ ТОКЕН"

        async def main():
            async with AsyncClient() as client:
                await logout(client, refresh_token)
        ```
    """
    await post(
        client,
        f"https://{domain}/api/v1/auth/logout",
        cookies={"refresh_token": refresh_token},
        **kwargs
    )


async def change_password(
        client: httpx.AsyncClient,
        access_token: str,
        old_password: str,
        new_password: str,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> None:
    """Поменять пароль. При успешной смене пароля `refresh_token` отзывается.

    Args:
        client: httpx.AsyncClient
        access_token: access токен
        old_password: старый пароль
        new_password: новый пароль
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации
        InvalidPasswordError: Пароль не подходит под условия
        InvalidOldPasswordError: Указан неверный старый пароль
        SomePasswordError: Новый пароль должен отличать от старого

    Examples:
        ```python
        from httpx import AsyncClient
        from aioitd.api import refresh, change_password

        refresh_token = "ВАШ ТОКЕН"
        password = "ВАШ ПАРОЛЬ"

        async def main():
            async with AsyncClient() as client:
                access_token = await refresh(client, refresh_token)
                await change_password(client, access_token, password, "НОВЫЙ ПАРОЛЬ")
        ```
    """
    await post(
        client,
        f"https://{domain}/api/v1/auth/change-password",
        json={"oldPassword": old_password, "newPassword": new_password},
        headers={"authorization": add_bearer(access_token)},
        **kwargs
    )


__all__ = ["change_password", "logout", "refresh"]
