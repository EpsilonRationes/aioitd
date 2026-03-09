import base64
import json
import time
from json import JSONDecodeError
from typing import Callable, Coroutine, Any

import httpx

from aioitd import ITDError, itd_codes, RateLimitError, ParamsValidationError, GatewayTimeOutError, \
    NotAllowedError, TooLargeError, NotFoundError, UnauthorizedError


def decode_jwt_payload(jwt_token: str) -> dict[str, Any]:
    """Декодирует pyload jwt.

    Args:
        jwt_token: jwt токен

    Returns:
        jwt payload
    """
    payload = jwt_token.split('.')[1]
    payload += '=' * ((4 - len(payload) % 4) % 4)
    decoded = base64.urlsafe_b64decode(payload).decode('utf-8')
    return json.loads(decoded)


def is_token_expired(access_token: str) -> bool:
    """Истёк ли `access_token`.

    Args:
        access_token: access токен

    Returns:
         Истёк ли токен

    """
    payload = decode_jwt_payload(access_token)
    return time.time() - 1 >= payload['exp']


def add_bearer(token: str):
    """Добавить Bearer к токену, если отсутствует."""
    if 'Bearer' not in token:
        return "Bearer " + token.strip()
    else:
        return token


async def request(
        method: Callable[..., Coroutine[None, None, httpx.Response]],
        url: str,
        **kwargs
) -> httpx.Response:
    result = await method(url, **kwargs)

    if result.text == "UNAUTHORIZED":
        raise UnauthorizedError
    if result.text == "NOT_FOUND":
        raise NotFoundError(NotFoundError.code, "Not found")
    if result.status_code == 413:
        raise TooLargeError(TooLargeError.code, "Размер запроса слишком большой")
    if result.status_code == 405:
        raise NotAllowedError(NotAllowedError.code, "Not Allowed")
    if result.status_code == 504:
        raise GatewayTimeOutError(GatewayTimeOutError.code, "504 Gateway Time-out")
    print(result.text)
    try:
        data = result.json()
        if 'type' in data:
            raise ParamsValidationError(type=data['type'], on=data['on'], found=data.get('found'))
        if 'error' in data:
            if 'retry_after' in data:
                raise RateLimitError(RateLimitError.code, data['error'], retry_after=data["retry_after"])
            if data['error'] == 'Too Many Requests':
                raise RateLimitError(RateLimitError.code, data['error'], retry_after=-1)
            error = data['error']
            if error['code'] == "RATE_LIMIT_EXCEEDED":
                raise RateLimitError(code=error['code'], message=error["message"], retry_after=error["retryAfter"])
            if error['code'] in itd_codes:
                ex = itd_codes[error['code']]
                message = ex.message if hasattr(ex, "message") else error['message']
                raise ex(ex.code, message)
            else:
                raise ITDError(code=error['code'], message=error["message"])
    except JSONDecodeError:
        if result.status_code != 204:
            raise ITDError("UNKNOWN", result.text)

    return result


async def get(
        client: httpx.AsyncClient,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        **kwargs
) -> httpx.Response:
    return await request(client.get, url, params=params, headers=headers, **kwargs)


async def post(
        client: httpx.AsyncClient,
        url: str, json: Any | None = None,
        params: dict | None = None,
        cookies: dict | None = None,
        files: dict | None = None,
        timeout: int | None = None,
        headers: dict | None = None,
        **kwargs,
) -> httpx.Response:
    return await request(
        client.post, url, json=json, params=params, cookies=cookies, files=files, timeout=timeout, headers=headers,
        **kwargs
    )


async def delete(
        client: httpx.AsyncClient,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        **kwargs
) -> httpx.Response:
    return await request(client.delete, url, params=params, headers=headers, **kwargs)


async def put(
        client: httpx.AsyncClient,
        url: str,
        json: Any | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        **kwargs
) -> httpx.Response:
    return await request(client.put, url, json=json, params=params, headers=headers, **kwargs)


async def patch(
        client: httpx.AsyncClient,
        url: str,
        json: Any | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        **kwargs
) -> httpx.Response:
    return await request(client.patch, url, json=json, params=params, headers=headers, **kwargs)


__all__ = ['delete', 'put', 'patch', 'post', 'get', 'request', 'add_bearer', 'is_token_expired', 'decode_jwt_payload']
