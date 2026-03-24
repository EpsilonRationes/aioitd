!!! example "Пример" 

    ```python 
    from aioitd import AsyncITDClient
    
    async def main():
        async with AsyncITDClient("ВАШ ТОКЕН") as client:
            post = await client.create_post("test")
            await post.like()
            await post.delete()
            await post.restore()
            await post.update("test updated")
            comment = await post.comment("test comment")
            await comment.like()
    
            post = client.post_ref(post.id)
            _, comments = await post.get_comments()
            await comments[0].unlike()
            await post.delete()
    
            user = client.user_ref("nowkie")
            _, posts = await user.get_liked_posts()
            for post in posts:
                _, comments = await post.get_comments()
                if len(comments) > 0:
                    print(comments[0].content)
            
            _, posts = await client.get_liked_posts(user)
    ```
