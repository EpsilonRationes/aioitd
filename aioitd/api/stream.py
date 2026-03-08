from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable
import json

import httpx
import httpx_sse

from aioitd.fetch import add_bearer
from aioitd.models.stream import SSEEvent, ConnectedEvent, NotificationEvent

ITD_SSE_PING = 15


async def _sse_wrapper(
        aiter_see: Callable[[], AsyncGenerator[httpx_sse.ServerSentEvent, None]]
) -> AsyncGenerator[ConnectedEvent | NotificationEvent | SSEEvent, None]:
    async for sse in aiter_see():
        if sse.event == "connected":
            event = ConnectedEvent(**json.loads(sse.data))
        elif sse.event == "notification":
            event = NotificationEvent(**json.loads(sse.data))
        else:
            event = SSEEvent(event=sse.event, data=sse.data)
        yield event


@asynccontextmanager
async def connect_notifications(
        client: httpx.AsyncClient,
        access_token: str,
        domain: str = "xn--d1ah4a.com"
) -> AsyncGenerator[AsyncGenerator[ConnectedEvent | NotificationEvent | SSEEvent, None], None]:
    """Подключиться к SEE стриму уведомлений.

    Args:
        client: httpx.AsyncClient
        access_token: access токен
        domain: домен

    Raises:
        SSEError: ошибка SSE

    Examples:

        async with connect_notifications(client, access_token) as events:
            async for event in events:
                if isinstance(event, NotificationEvent):
                    print(event)
    """
    async with httpx_sse.aconnect_sse(
            client, "GET", f"https://{domain}/api/notifications/stream",
            headers={"authorization": add_bearer(access_token)},
            timeout=httpx.Timeout(
                connect=30.0,
                read=ITD_SSE_PING + 1,
                write=30.0,
                pool=30.0
            ),
    ) as event_source:
        yield _sse_wrapper(event_source.aiter_sse)


__all__ = ['connect_notifications']
