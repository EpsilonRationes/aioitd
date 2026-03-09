# aioitd

Асинхронный Python клиент для итд.com

документация: https://EpsilonRationes.github.io/aioitd/

## Установка

```bash
pip install aioitd
```

## Без авторизации

Апи хештегов доступно без авторизации.

```python
from aioitd import AsyncITDClient
import asyncio


async def main():
    async with AsyncITDClient() as client:
        hashtags = await client.search_hashtags('a')
        for hashtag in hashtags:
            print(f"#{hashtag.name}: {hashtag.posts_count}")

asyncio.run(main())
```

## Авторизация

Для остальных функций необходим `refresh_token`

Чтобы получить refresh_token:
1. Войди в аккаунт на итд.com 
2. Откройть devtools
3. Среди табов выбрать network (сеть)
4. Перезагрузить страницу
5. Найти запрос `refresh`
6. В куки запроса скопировать `refresh_token`

Или:
1. Войти в аккаунт на итд.com
2. Откройть devtools
3. Среди табов выбрать application (приложение)
4. Перезагрузить страницу
5. Выбрать куки и найти куку `refersh_token`

После передайте `refresh_token` в `AsyncITDClient`:

```python
from aioitd import AsyncITDClient
import asyncio

refresh_token = "ca1291a4a990b985a57b880ed3fb863eef80ac3990acc68e8f106a783e3af402"

async def main():
    async with AsyncITDClient(refresh_token) as client:
        user = await client.get_user("nowkie")
        print(
            f"id: {user.id}\n"
            f"username: {user.username}\n"
            f"follower_count: {user.followers_count}"
        )

asyncio.run(main())
```

### Создание поста

```python 
from aioitd import AsyncITDClient, File, Post
import asyncio
from uuid import UUID

refresh_token = "ВАШ ТОКЕН"

async def main():
    async with AsyncITDClient(refresh_token) as client:
        images_path = ["sun.png", "снег.gif", "python.jpg"]
        files_ids: list[UUID] = []
        for path in images_path:
            with open(path, 'rb') as f:
                file: File = await client.upload_file(f)
                files_ids.append(file.id)
        post: Post = await client.create_post("ТЕКСТ ПОСТА", attachment_ids=files_ids)


asyncio.run(main())
```

### Поменять баннер

```python
async def main():
    async with AsyncITDClient(refresh_token) as client:
        with open(r"file.gif", 'rb') as file:
            image = await client.upload_file(file)
        await client.update_profile(banner_id=image.id)
```

### Уведомления по SSE 

```python
from aioitd import NotificationEvent, ConnectedEvent

async def main():
    async with AsyncITDClient(refresh_token) as itd:
        async with itd.connect_sse() as events:
            async for event in events:
                if isinstance(event, ConnectedEvent):
                    print("Прослушка начата")
                elif isinstance(event, NotificationEvent):
                    print(event.actor)

asyncio.run(main())
```


## RateLimitError

`RateLimitError` ограничение по количеству запросов.
`retray_after` — через сколько можно повторить запрос.

```python 
while True:
    try:
        await client.post("content")
    except RateLimitError as ex:
        await asyncio.sleep(ex.retry_after)
```


Автор в итд [@FIRST_TM](https://итд.com/@FIRST_TM)
