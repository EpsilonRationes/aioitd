import typing
from typing import Optional, Annotated

from pydantic import ConfigDict, Field

from aioitd.models.base import ITDBaseModel
from aioitd.objects.base import require_client

if typing.TYPE_CHECKING:
    from aioitd.client import AsyncITDClient
    from aioitd.models import Pagination, Post, Comment, Hashtag


class HashtagRef(ITDBaseModel):
    name: str
    client: Annotated[Optional['AsyncITDClient'], Field(exclude=True)] = None

    model_config = ConfigDict(
        **ITDBaseModel.model_config,
        arbitrary_types_allowed=True
    )

    def __init__(self, name: str | None = None, client: Optional['AsyncITDClient'] = None, **data):
        if name is not None:
            data['name'] = name
        if client is not None:
            data['client'] = client
        super().__init__(**data)

    def _get_name(self) -> str:
        return self.name

    @require_client
    async def get_posts(
        self,
        cursor: str | None = None,
        limit: int = 20,
        **kwargs
    ) -> tuple[Hashtag, Pagination, list[tuple[list[Comment], Post]]]:
        """Посты по этому хештегу.

        Args:
            cursor: next_cursor предыдущей страницы
            limit: максимальное количество выданных постов (1 <= limit <= 50)

        Returns:
            хештег, пагинация, список из постов и их комментариев

        Raises:
            NotFoundError: Хештег не найден
        """
        return await self.client.get_posts_by_hashtag(self._get_name(), cursor, limit, **kwargs)


__all__ = ['HashtagRef']