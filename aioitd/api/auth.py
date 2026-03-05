from aioitd.fetch import add_bearer, post
import httpx


async def refresh(
    client: httpx.AsyncClient,
    refresh_token: str,
    domain: str = "xn--d1ah4a.com"
) -> str:
    """Получить access_token.

    Args:
        client: httpx.AsyncClient
        refresh_token: refresh токен
        domain: домен

    Returns: access токен

    Raises:
        TokenNotFoundError: Такого токена не существует
        TokenRevokedError: Токен отозван
        TokenMissingError: Токен не указан (равен пустой строке)
        TokenExpiredError: Токен истёк
    """
    response = await post(
        client,
        f"https://{domain}/api/v1/auth/refresh",
        cookies={"refresh_token": refresh_token}
    )
    return response.json()["accessToken"]


async def logout(
    client: httpx.AsyncClient,
    refresh_token: str,
    domain: str = "xn--d1ah4a.com"
) -> None:
    """Выйти из аккаунта, отозвать токен. Работает при любом токене. Просроченном, не существующем и пустой строкой тоже.

    Args:
        client: httpx.AsyncClient
        refresh_token: refresh токен
        domain: домен
    """
    await post(
        client,
        f"https://{domain}/api/v1/auth/logout",
        cookies={"refresh_token": refresh_token}
    )


async def change_password(
        client: httpx.AsyncClient,
        access_token: str,
        old_password: str,
        new_password: str,
        domain: str = "xn--d1ah4a.com"
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

    """
    await post(
        client,
        f"https://{domain}/api/v1/auth/change-password", 
        json={"oldPassword": old_password, "newPassword": new_password},
        headers={"authorization": add_bearer(access_token)}
    )
