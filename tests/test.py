import asyncio
from uuid import uuid8

from aioitd import AsyncITDClient, ValidationError, TooLargeError, UploadError, NotFoundError, FetchInterval, BoldSpan, SpoilerSpan, MentionSpan, HashTagSpan

from setting import refresh_token as refresh_token1, refresh_token2

random_id = uuid8()
image_id = "c63a2cf7-3c6d-46d4-bfde-634067603e73" # чужое изображение
not_many_hashtag = "femboy" # не очень популярный хештег

async def test_file():
    itd1 = AsyncITDClient(refresh_token1)

    with open("image.jpg", 'rb') as file:
       image = await itd1.upload_file(file)
    with open("audio.mp3", 'rb') as file:
       audio = await itd1.upload_file(file)
    with open("video.mov", 'rb') as file:
       video = await itd1.upload_file(file)

    try:
        with open("abc.txt", 'rb') as file:
            text = await itd1.upload_file(file)
    except ValidationError:
        pass

    try:
        with open("large_file.mp4", "rb") as file:
            await itd1.upload_file(file)
    except TooLargeError:
        pass

    try:
        with open("abc.png", 'rb') as file:
            await itd1.upload_file(file)
    except UploadError:
        pass

    file = await itd1.get_file(image_id)

    try:
        file = await itd1.get_file(random_id)
    except NotFoundError:
        pass

    await itd1.delete_file(image.id)
    await itd1.delete_file(audio.id)
    await itd1.delete_file(video.id)

    try:
        await itd1.delete_file(random_id)
    except NotFoundError:
        pass

    try:
        await itd1.delete_file(image_id)
    except NotFoundError:
        pass

    await itd1.close()


async def test_hashtags():
    itd1 = AsyncITDClient(refresh_token1, time_delta=1, timeout=20)

    hashtags = await itd1.get_trending_hashtags()
    hashtags = await itd1.get_trending_hashtags(20)

    try:
        hashtags = await itd1.get_trending_hashtags(51)
    except ValidationError:
        pass

    try:
        hashtags = await itd1.get_trending_hashtags(0)
    except ValidationError:
        pass

    hashtags = await itd1.search_hashtags("")
    hashtags = await itd1.search_hashtags("8", limit=20)

    try:
        hashtags = await itd1.search_hashtags2("1"*1001)
    except ValidationError:
        pass


    cursor = None
    while True:
        hashtag, pagination, hashtags = await itd1.get_posts_by_hashtag(not_many_hashtag, cursor=cursor, limit=1)
        cursor = pagination.next_cursor
        if cursor is None:
            break

    try:
        hashtags = await itd1.search_hashtags("8", 51)
    except ValidationError:
        pass

    try:
        hashtags = await itd1.get_posts_by_hashtag("")
    except NotFoundError:
        pass

    try:
        hashtags = await itd1.get_posts_by_hashtag("!")
    except NotFoundError:
        pass

    try:
        hashtags = await itd1.get_posts_by_hashtag("8", limit=51)
    except ValidationError:
        pass

    await itd1.close()


text_post_id = "e99d502f-1e6e-4909-8686-790bbaa379aa"
post_with_audio = "b0fc8ad2-32b3-42cb-bd8d-6e92e8a302cf"
post_with_image = "125016a0-8bb5-49d1-a2f9-590b349c5147"
post_with_video = "d96edabe-8486-446e-9709-6f0dfad3a333"
post_reposted = "60c1571c-aeae-4d55-9390-2ba8d8a744fd"
post_with_comments = "50f9d2de-655e-49cf-8939-9f330eeaad06"
post_with_all_type_comments = "d96edabe-8486-446e-9709-6f0dfad3a333"

async def test_posts():
    interval = FetchInterval(0.2)
    itd1 = AsyncITDClient(refresh_token1, time_delta=interval)
    itd2 = AsyncITDClient(refresh_token2, time_delta=interval)
    cursor = None
    for _ in range(5):
        pagination, posts = await itd1.get_popular_posts(cursor)
        cursor = pagination.next_cursor
        if cursor is None:
            break
    pagination, posts = await itd1.get_popular_posts(1000)

    try:
        await itd1.get_popular_posts(limit=51)
    except ValidationError:
        pass

    cursor = None
    for _ in range(5):
        pagination, posts = await itd1.get_following_posts(cursor)
        cursor = pagination.next_cursor
        if cursor is None:
            break

    try:
        await itd1.get_following_posts(limit=51)
    except ValidationError:
        pass

    post = await itd1.get_post(text_post_id)
    post = await itd1.get_post(post_with_image)
    post = await itd1.get_post(post_with_audio)
    post = await itd1.get_post(post_with_video)
    post = await itd1.get_post(post_reposted)

    try:
        post = await itd1.get_post(random_id)
    except NotFoundError:
        pass

    for sort in ['new', 'popular']:
        cursor = None
        for _ in range(10):
            pagination, posts = await itd1.get_posts_by_user("nowkie", sort=sort, cursor=cursor)
            cursor = pagination.next_cursor
            if cursor is None:
                break

    for _ in range(10):
        cursor = None
        for _ in range(10):
            pagination, posts = await itd1.get_posts_by_user_newest("nowkie", cursor=cursor)
            cursor = pagination.next_cursor
            if cursor is None:
                break

    cursor = None
    for _ in range(10):
        pagination, posts = await itd1.get_posts_by_user_popular("nowkie", cursor=cursor)
        cursor = pagination.next_cursor
        if cursor is None:
            break

    try:
        pagination, posts = await itd1.get_posts_by_user("!")
    except NotFoundError:
        pass

    try:
        pagination, posts = await itd1.get_posts_by_user_newest("!")
    except NotFoundError:
        pass

    try:
        pagination, posts = await itd1.get_posts_by_user_popular("!")
    except NotFoundError:
        pass


    try:
        pagination, posts = await itd1.get_posts_by_user("")
    except NotFoundError:
        pass

    try:
        pagination, posts = await itd1.get_posts_by_user_newest("")
    except NotFoundError:
        pass

    try:
        pagination, posts = await itd1.get_posts_by_user_popular("")
    except NotFoundError:
        pass

    cursor = None
    for _ in range(10):
        pagination, posts = await itd1.get_posts_by_user_liked("nowkie", cursor=cursor)
        cursor = pagination.next_cursor
        if cursor is None:
            break

    try:
        pagination, posts = await itd1.get_posts_by_user_liked("!")
    except NotFoundError:
        pass

    try:
        pagination, posts = await itd1.get_posts_by_user_liked("")
    except NotFoundError:
        pass

    cursor = None
    for _ in range(10):
        pagination, posts = await itd1.get_posts_by_user_wall("blue_cir", cursor=cursor, limit=1)
        cursor = pagination.next_cursor
        if cursor is None:
            break

    try:
        pagination, posts = await itd1.get_posts_by_user_wall("!")
    except NotFoundError:
        pass

    try:
        pagination, posts = await itd1.get_posts_by_user_wall("")
    except NotFoundError:
        pass

    for sort in ["popular", "newest", "oldest"]:
        cursor = None
        for _ in range(10):
            pagination, posts = await itd1.get_post_comments(post_with_comments, cursor=cursor, sort=sort)
            cursor = pagination.next_cursor
            if cursor is None:
                break

    try:
        pagination, posts = await itd1.get_post_comments(random_id)
    except NotFoundError:
        pass

    cursor = None
    for _ in range(10):
        pagination, posts = await itd1.get_post_newest_comments(post_with_comments, cursor=cursor)
        cursor = pagination.next_cursor
        if cursor is None:
            break

    cursor = None
    for _ in range(10):
        pagination, posts = await itd1.get_post_oldest_comments(post_with_comments, cursor=cursor)
        cursor = pagination.next_cursor
        if cursor is None:
            break

    cursor = None
    for _ in range(10):
        pagination, posts = await itd1.get_post_popular_comments(post_with_comments, cursor=cursor)
        cursor = pagination.next_cursor
        if cursor is None:
            break

    pagination, posts = await itd1.get_post_comments(post_with_all_type_comments)

    text_post = await itd1.create_post("Test post")

    with open("image.jpg", 'rb') as file:
        image = await itd1.upload_file(file)

    image_post = await itd1.create_post("", [image.id])

    with open("video.mov", 'rb') as file:
        video = await itd1.upload_file(file)

    video_post = await itd1.create_post("", [video.id])

    with open("audio.mp3", 'rb') as file:
        audio = await itd1.upload_file(file)

    audio_post = await itd1.create_post("", [audio.id])

    repost = await itd2.repost(text_post.id)

    await itd1.delete_post(text_post.id)

    deleted_post_respot = await itd1.get_post(repost.id)

    await itd1.delete_post(text_post.id)
    await itd1.delete_post(image_post.id)
    await itd1.delete_post(video_post.id)
    await itd2.delete_post(repost.id)

    with open("image.jpg", 'rb') as file:
        image = await itd1.upload_file(file)

    image_post = await itd1.create_post("", [image.id])
    await itd1.update_post(image_post.id, "test, 2")
    try:
        await itd1.update_post(image_post.id, "")
    except ValidationError:
        pass

    await itd1.pin_post(image_post.id)
    await itd1.unpin_post(image_post.id)

    await itd1.view_post(image_post.id)
    await itd1.like_post(image_post.id)
    await itd1.delete_like_post(image_post.id)

    await itd1.delete_post(image_post.id)
    await itd1.restore_post(image_post.id)
    await itd1.delete_post(image_post.id)

    await itd1.close()
    await itd2.close()

    text_comment = await itd1.comment(text_post_id, "text")

    await itd1.delete_comment(text_comment.id)
    await itd1.restore_comment(text_comment.id)
    await itd1.like_comment(text_comment.id)
    await itd1.delete_like_comment(text_comment.id)
    await itd1.delete_comment(text_comment.id)

    with open("image.jpg", 'rb') as file:
        image = await itd1.upload_file(file)

    image_comment = await itd1.comment(text_post_id, "", [image.id])

    await itd1.delete_comment(image_comment.id)


async def test_poll():
    itd1 = AsyncITDClient(refresh_token1)

    post = await itd1.create_post("", question="Test question", options=["option1", "option2"])
 
    try: 
        post = await itd1.create_post("", question="1"*129, options=["option1", "option2"])
    except ValidationError:
        pass
    
    try:
        post = await itd1.create_post("", question="for_test", options=["option1"]*1)
    except ValidationError:
        pass 

    try:
        post = await itd1.create_post("", question="for_test", options=[""]*2)
    except ValidationError:
        pass

    await itd1.close()


async def test_spans():
    itd1 = AsyncITDClient(refresh_token1)
    
    post = await itd1.create_post(
        "Крутите барабан! мелочёвка", 
        spans=[SpoilerSpan(offset=len("Крутите барабан! ")+i, length=1) for i in range(9)] + [SpoilerSpan(offset=len("Крутите барабан! "), length=9)]
    )
    await itd1.delete_post(post.id)

    try:
        post = await itd1.create_post(
            "Сколько споллеров можно повесить на одну букву? Ъ",
            spans=[SpoilerSpan(offset=len("Сколько споллеров можно повесить на одну букву? "), length=1) for i in range(101)]
        )
    except ValidationError:
        pass

    
    await itd1.close()


async def test_users():
    itd1 = AsyncITDClient(refresh_token1)

    user = await itd1.get_user("nowkie")
    me = await itd1.get_me()
    
    await itd1.close()


async def test_privacy():
    itd1 = AsyncITDClient(refresh_token1)

    privacy = await itd1.get_privacy()

    privacy = await itd1.update_privacy(is_private=True)
    privacy = await itd1.update_privacy(is_private=False)


post_with_vote = "758f912e-65fa-4db2-9e68-ce33c70460d7"

async def test_vote():
    itd1 = AsyncITDClient(refresh_token1)

    post = await itd1.get_post(post_with_vote)

    poll = await itd1.vote(post.id, [post.poll.options[0].id])
    poll = await itd1.vote(post.id, [post.poll.options[0].id])

    try:
        poll = await itd1.vote(random_id, [post.poll.options[0].id])
    except NotFoundError:
        pass

    try:
        poll = await itd1.vote(post.id, [random_id])
    except ValidationError:
        pass

    try:
        poll = await itd1.vote(post.id, [post.poll.options[0].id, post.poll.options[1].id])
    except ValidationError:
        pass
    try:
        poll = await itd1.vote(post.id, [])
    except ValidationError:
        pass

    await itd1.close()


if __name__ == '__main__':
    asyncio.run(test_vote())
