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


__all__ = ['get_changelog']
