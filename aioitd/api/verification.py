import httpx

from aioitd.fetch import add_bearer, get, post


async def get_verification_status(
        client: httpx.AsyncClient,
        access_token: str,
        domain: str = "xn--d1ah4a.com"
) -> str:
    """Получить статус верификации
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации

    """
    response = await get(
        client,
        f"https://{domain}/api/verification/status",
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()
    return data["status"]


async def submit_verification(
        client: httpx.AsyncClient,
        access_token: str,
        video_url: str,
        domain: str = "xn--d1ah4a.com"
) -> dict:
    """Подать запрос на галочку
    
    Args:
        client: httpx.AsyncClient
        access_token: access токен
        video_url: url видео, загруженного на itd
        domain: домен

    Raises:
        UnauthorizedError: ошибка авторизации

    """
    response = await post(
        client,
        f"https://{domain}/api/verification/submit",
        json={"videoUrl": video_url},
        headers={"authorization": add_bearer(access_token)}
    )
    data = response.json()
    return data


__all__ = [get_verification_status, submit_verification]
