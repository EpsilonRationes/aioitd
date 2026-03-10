# Форматирование текста

!!! Example "пример"

    ```python 
    from aioitd import AsyncITDClient
    from aioitd.parser import parse
    
    refresh_token = "ВАШ ТОКЕН"
    
    async def main():
        async with AsyncITDClient(refresh_token) as client:
            await client.create_post(**parse(
                "Наша компания [https://comapy.com]() сопровождает несколько интернет‑магазинов на платформе **Битрикс**, "
                "каждый из которых включает <b>собственную</b> ||линейку|| программных решений. По всем "
                "продуктам необходимо [составлять](https://example.com) и публиковать актуальную документацию."
            ))
    ```

::: aioitd.parser
    options:
        show_root_heading: true
        members:
            - ParseResult
            - parse_html
            - parse_md
            - parse