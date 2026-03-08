# api

Модуль `api` содержит функции для запросов к итд.com.

```python 
from aioitd.api import something
```

Общий вид функций модуля:

```
function(
    client: httpx.AsyncClient, 
    access_token: str, 
    ..., 
    domain: str = "xn--d1ah4a.com", 
    **kwargs
 )
```

!!! info "Примечание"

    - `logout` и `refresh` принимают `refresh_token` вместо `access_token`
    - апи хештегов не требует авторизации, поэтому `access_token` отсуствует 

!!! example "Пример" 

    ```python 
    from httpx import AsyncClient
    from aioitd.api import refresh, get_user, search_hashtags
    
    refresh_token = "ВАШ ТОКЕН"
    
    async def main():
        async with AsyncClient() as client:
            hashtags = await search_hashtags(client, 'a')
            access_token = await refresh(client, refresh_token)
            user = await get_user(client, access_token, 'nowkie')
    ```

kwargs — дополнительные параметры, которые будут переданные в функцию httpx get, post, put итд.

!!! example "Пример" 

    ```python
    from httpx import AsyncClient
    from aioitd.api import refresh, upload_file 
    
    refresh_token = "ВАШ ТОКЕН"
    
    async def main():
        async with AsyncClient() as client:
            access_token = await refresh(client, refresh_token)
            with open('file.png', 'rb') as f:
                user = await upload_file(client, access_token, f, timeout=100)
    ```
