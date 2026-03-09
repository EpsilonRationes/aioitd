# aioitd

Асинхронный Python клиент для итд.com

Пример:

```python 
from aioitd import AsyncITDClient, File, Post
import asyncio
from uuid import UUID

refresh_token = "ca1291a4a990b985a57b880ed3fb863eef80ac3990acc68e8f106a783e3af402"

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
