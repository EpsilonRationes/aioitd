import httpx

from aioitd.fetch import get
from aioitd.models.platform import Version


async def get_changelog(
        client: httpx.AsyncClient,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> list[Version]:
    """Получить чейнджлог.

    Args:
        client: httpx.AsyncClient
        domain: домен

    """
    response = await get(
        client,
        f"https://{domain}/api/platform/changelog",
        **kwargs
    )
    data = response.json()['data']
    return list(map(Version.model_validate, data))


async def get_portal(
        client: httpx.AsyncClient,
        domain: str = "xn--d1ah4a.com",
        **kwargs
) -> bool:
    """Активен ли портал

    Args:
        client: httpx.AsyncClient
        domain: домен

    Returns:
        Активен ли портал

    """
    response = await get(
        client,
        f"https://{domain}/api/v1/portal",
        **kwargs
    )
    data = response.json()
    return data['active']


__all__ = ['get_changelog', 'get_portal']
