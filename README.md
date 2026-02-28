# aioitd

Асинхронный Python клиент для итд.com

# Установка

```commandline
pip install aioitd
```

# Пример

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
4. Выбрать куки и скопировать токен

# AsyncITDClient

Автоматически вызывает `refersh`, по окончании срока жизни access токена. 

```python
async with AsyncITDClient(refresh_token) as client:
```

или

```python 
client = AsyncITDClient(refresh_token)
...
await client.close()
```



# Создание поста 

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

# Поменять баннер

```python
async def main():
    async with AsyncITDClient(refresh_token) as client:
        with open(r"file.gif", 'rb') as file:
            image = await client.upload_file(file)
        await client.update_profile(username="aioitd", banner_id=image.id)
```

# Error429 и RateLimitError

`Error429` возникает из-за ограничения количества запросов на сервер. Чтобы обойти, нужно соблюдать интервал между запросами.
Его можно указать в `time_delta`, и по умолчанию он равен 0.105 секунд. 

```python
async with AsyncITDClient(refresh_token, time_delta=1)
```

Чтобы отключить задержку между запросами:

```python 
async with AsyncITDClient(refresh_token, time_delta=None)
```


`RateLimitError` ограничение по количеству определённых действий для каждого аккаунта.
`retray_after` — через сколько можно повторить запрос.

```python 
while True:
    try:
        await client.post("content")
    except RateLimitError as ex:
        await asyncio.sleep(ex.retry_after)
```

# Уведомления по SSE 

```python
async def main():
    async with AsyncITDClient(refresh_token) as itd:
        async with itd.connect_sse() as events:
            async for event in events:
                print(event)

asyncio.run(main())
```

Автор в итд [@FIRST_TM](https://итд.com/@FIRST_TM)
