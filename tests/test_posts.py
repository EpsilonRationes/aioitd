from uuid import uuid8

from aioitd import AsyncITDClient, ValidationError, \
    NotFoundError, ForbiddenError, NotPinedError, ConflictError
import unittest

from tests import assert_async_raises
from tests.setting import refresh_token, refresh_token2, post_id, deleted_post_id


class TestPosts(unittest.IsolatedAsyncioTestCase):
    async def test_get_popular_posts(self):
        async with AsyncITDClient(refresh_token) as client:
            pagination, posts = await client.get_popular_posts()

    @assert_async_raises(ValidationError)
    async def test_get_popular_posts_limit(self):
        async with AsyncITDClient(refresh_token) as client:
            pagination, posts = await client.get_popular_posts(limit=51)

    async def test_get_following_posts(self):
        async with AsyncITDClient(refresh_token) as client:
            pagination, posts = await client.get_following_posts()

    @assert_async_raises(ValidationError)
    async def test_get_following_posts_limit(self):
        async with AsyncITDClient(refresh_token) as client:
            pagination, posts = await client.get_following_posts(limit=51)

    async def test_get_post(self):
        async with AsyncITDClient(refresh_token) as client:
            posts = await client.get_post(post_id)

    @assert_async_raises(NotFoundError)
    async def test_get_deleted_post(self):
        async with AsyncITDClient(refresh_token) as client:
            posts = await client.get_post(deleted_post_id)

    @assert_async_raises(NotFoundError)
    async def test_get_post_not_found(self):
        async with AsyncITDClient(refresh_token) as client:
            posts = await client.get_post(uuid8())

    async def test_delete_post(self):
        async with AsyncITDClient(refresh_token) as client:
            post = await client.create_post("port_for_test")
            await client.delete_post(post.id)

    @assert_async_raises(NotFoundError)
    async def test_delete_post_not_found(self):
        async with AsyncITDClient(refresh_token) as client:
            await client.delete_post(uuid8())

    async def test_delete_forbidden(self):
        async with AsyncITDClient(refresh_token2) as client2:
            post = await client2.create_post("post_for_test")
            try:
                async with AsyncITDClient(refresh_token) as client:
                    await client.delete_post(post.id)
            except ForbiddenError:
                pass
            else:
                self.fail("ForbiddenError не выброшено")
            await client2.delete_post(post.id)

    async def test_restore_post(self):
        async with AsyncITDClient(refresh_token) as client:
            post = await client.create_post("port_for_test")
            await client.delete_post(post.id)
            await client.restore_post(post.id)

    async def test_restore_not_deleted_post(self):
        async with AsyncITDClient(refresh_token) as client:
            post = await client.create_post("port_for_test")
            await client.restore_post(post.id)
            await client.delete_post(post.id)

    @assert_async_raises(ValidationError)
    async def test_restore_not_found_post(self):
        async with AsyncITDClient(refresh_token) as client:
            await client.restore_post(uuid8())

    async def test_restore_forbidden_post(self):
        async with AsyncITDClient(refresh_token2) as client2:
            post = await client2.create_post("post_for_test")
            try:
                async with AsyncITDClient(refresh_token) as client:
                    await client.restore_post(post.id)
            except ForbiddenError:
                pass
            else:
                self.fail("ForbiddenError не выброшено")
            await client2.delete_post(post.id)

    async def test_like_post(self):
        async with AsyncITDClient(refresh_token) as client:
            post = await client.create_post("port_for_test")
            await client.like_post(post.id)
            await client.like_post(post.id)
            await client.delete_like_post(post.id)
            await client.delete_like_post(post.id)
            await client.delete_post(post.id)

    @assert_async_raises(NotFoundError)
    async def test_like_not_found(self):
        async with AsyncITDClient(refresh_token) as client:
            await client.like_post(uuid8())

    @assert_async_raises(NotFoundError)
    async def test_delete_like_not_found(self):
        async with AsyncITDClient(refresh_token) as client:
            await client.delete_like_post(uuid8())

    async def test_view_post(self):
        async with AsyncITDClient(refresh_token) as client:
            post = await client.create_post("port_for_test")
            await client.view_post(post.id)
            await client.view_post(post.id)
            await client.delete_like_post(post.id)

    async def test_view_post_not_found(self):
        async with AsyncITDClient(refresh_token) as client:
            await client.view_post(uuid8())

    async def test_pin_post(self):
        async with AsyncITDClient(refresh_token) as client:
            post = await client.create_post("port_for_test")
            await client.pin_post(post.id)
            await client.pin_post(post.id)
            await client.delete_like_post(post.id)

    @assert_async_raises(NotFoundError)
    async def test_pin_post_not_found(self):
        async with AsyncITDClient(refresh_token) as client:
            await client.pin_post(uuid8())

    async def test_pin_post_forbidden(self):
        async with AsyncITDClient(refresh_token2) as client2:
            post = await client2.create_post("post_for_test")
            try:
                async with AsyncITDClient(refresh_token) as client:
                    await client.pin_post(post.id)
            except ForbiddenError:
                pass
            else:
                self.fail("ForbiddenError не выброшено")
            await client2.delete_post(post.id)

    async def test_unpin_post(self):
        async with AsyncITDClient(refresh_token) as client:
            post = await client.create_post("port_for_test")
            await client.pin_post(post.id)
            await client.unpin_post(post.id)
            await client.delete_like_post(post.id)

    @assert_async_raises(NotFoundError)
    async def test_unpin_post_not_found(self):
        async with AsyncITDClient(refresh_token) as client:
            await client.unpin_post(uuid8())

    async def test_unpin_post_forbidden(self):
        async with AsyncITDClient(refresh_token2) as client2:
            post = await client2.create_post("post_for_test")
            await client2.pin_post(post.id)
            try:
                async with AsyncITDClient(refresh_token) as client:
                    await client.unpin_post(post.id)
            except NotPinedError:
                pass
            else:
                self.fail("NotPinedError не выброшено")
            await client2.delete_post(post.id)

    async def test_repost(self):
        async with AsyncITDClient(refresh_token2) as client2:
            post2 = await client2.create_post("post_for_test")
            async with AsyncITDClient(refresh_token) as client:
                post = await client.repost(post2.id)
                await client.delete_post(post.id)
            await client2.delete_post(post2.id)

    async def test_repost_post_many(self):
        async with AsyncITDClient(refresh_token2) as client2:
            post2 = await client2.create_post("post_for_test")
            try:
                async with AsyncITDClient(refresh_token) as client:
                    post = await client.repost(post2.id)
                    post = await client.repost(post2.id)
                    await client.delete_post(post.id)
            except ConflictError:
                pass
            else:
                self.fail("ConflictError не выброшено")
            await client2.delete_post(post2.id)

    async def test_repost_self(self):
        async with AsyncITDClient(refresh_token) as client:
            post = await client.create_post("port_for_test")
            try:
                repost = await client.repost(post.id)
                await client.delete_post(repost.id)
            except ValidationError:
                pass
            else:
                self.fail("ValidationError не выброшено")
            await client.delete_post(post.id)

    async def test_repost_content(self):
        async with AsyncITDClient(refresh_token2) as client2:
            post2 = await client2.create_post("port_for_test")
            try:
                async with AsyncITDClient(refresh_token) as client:
                    post = await client.repost(post2.id, "0" * 5_001)
            except ValidationError:
                pass
            else:
                self.fail("ValidationError не выброшено")
            await client2.delete_post(post2.id)

    async def test_get_post_by_user(self):
        async with AsyncITDClient(refresh_token) as client:
            pagination, posts = await client.get_posts_by_user("nowkie")

    @assert_async_raises(NotFoundError)
    async def test_get_post_by_user_not_found(self):
        async with AsyncITDClient(refresh_token) as client:
            pagination, posts = await client.get_posts_by_user("n")

    async def test_get_post_by_popular(self):
        async with AsyncITDClient(refresh_token) as client:
            pagination, posts = await client.get_posts_by_user_popular("nowkie")

    async def test_get_posts_by_user_liked(self):
        async with AsyncITDClient(refresh_token) as client:
            pagination, posts = await client.get_posts_by_user_liked("nowkie")

    async def test_get_posts_by_user_wall(self):
        async with AsyncITDClient(refresh_token) as client:
            pagination, posts = await client.get_posts_by_user_wall("nowkie")

    async def test_get_post_comments(self):
        async with AsyncITDClient(refresh_token) as client:
            for sort in ["popular", "newest", "oldest"]:
                pagination, comments = await client.get_post_comments(post_id, sort=sort)

    async def test_create_post(self):
        async with AsyncITDClient(refresh_token) as client:
            post = await client.create_post("port_for_test")
            await client.delete_post(post.id)

    @assert_async_raises(ValidationError)
    async def test_create_post_content(self):
        async with AsyncITDClient(refresh_token) as client:
            post = await client.create_post('0' * 5_001)
            await client.delete_post(post.id)

    async def test_create_post_attachments(self):
        async with AsyncITDClient(refresh_token) as client:
            post = await client.create_post("", attachment_ids=[uuid8(), uuid8()])
            await client.delete_post(post.id)

    @assert_async_raises(ValidationError)
    async def test_create_post_blank(self):
        async with AsyncITDClient(refresh_token) as client:
            post = await client.create_post("")
            await client.delete_post(post.id)

    @assert_async_raises(ValidationError)
    async def test_create_post_attachments_max_len(self):
        async with AsyncITDClient(refresh_token) as client:
            post = await client.create_post("", attachment_ids=[uuid8()] * 100)
            await client.delete_post(post.id)

    async def test_update_post(self):
        async with AsyncITDClient(refresh_token) as client:
            post = await client.create_post("for_test")
            content = await client.update_post(post.id, "for_test2")
            await client.delete_post(post.id)

    async def test_update_post_some_content(self):
        async with AsyncITDClient(refresh_token2) as client2:
            post2 = await client2.create_post("for_test")
            try:
                async with AsyncITDClient(refresh_token) as client:
                    post = await client.create_post("for_test")
                    content = await client.update_post(post2.id, "for_test")
                    await client.delete_post(post.id)
            except ForbiddenError:
                pass
            else:
                self.fail("ForbiddenError не выброшено")
            await client2.delete_post(post2.id)

    async def test_comment(self):
        async with AsyncITDClient(refresh_token) as client:
            post = await client.create_post("for_test")
            comment = await client.comment(post.id, "test_comment")
            await client.delete_post(post.id)

    @assert_async_raises(ValidationError)
    async def test_comment_blank(self):
        async with AsyncITDClient(refresh_token) as client:
            post = await client.create_post("for_test")
            comment = await client.comment(post.id, "")
            await client.delete_post(post.id)

    @assert_async_raises(ValidationError)
    async def test_comment_attachments_max_len(self):
        async with AsyncITDClient(refresh_token) as client:
            post = await client.create_post("for_test")
            comment = await client.comment(post.id, "r", [uuid8()] * 5)
            await client.delete_post(post.id)

    async def test_delete_comment(self):
        async with AsyncITDClient(refresh_token) as client:
            post = await client.create_post("for_test")
            comment = await client.comment(post.id, "r")
            await client.delete_comment(comment.id)
            await client.delete_post(post.id)

    @assert_async_raises(NotFoundError)
    async def test_delete_comment_not_found(self):
        async with AsyncITDClient(refresh_token) as client:
            await client.delete_comment(uuid8())

    async def test_delete_comment_forbidden(self):
        async with AsyncITDClient(refresh_token2) as client2:
            post = await client2.create_post("for_test")
            comment = await client2.comment(post.id, "r")
            try:
                async with AsyncITDClient(refresh_token) as client:
                    await client.delete_comment(comment.id)
            except ForbiddenError:
                pass
            else:
                self.fail("ForbiddenError не выброшено")
            await client2.delete_post(post.id)

    async def test_comment_restore(self):
        async with AsyncITDClient(refresh_token) as client:
            post = await client.create_post("for_test")
            comment = await client.comment(post.id, "r")
            await client.delete_comment(comment.id)
            await client.restore_comment(comment.id)
            await client.delete_post(post.id)

    @assert_async_raises(NotFoundError)
    async def test_comment_restore_not_found(self):
        async with AsyncITDClient(refresh_token) as client:
            await client.restore_comment(uuid8())

    async def test_comment_restore_not_deleted(self):
        async with AsyncITDClient(refresh_token) as client:
            post = await client.create_post("for_test")
            comment = await client.comment(post.id, "r")
            await client.restore_comment(comment.id)
            await client.delete_post(post.id)

    async def test_comment_restore_forbidden(self):
        async with AsyncITDClient(refresh_token2) as client2:
            async with AsyncITDClient(refresh_token) as client:
                post = await client.create_post("for_test")
                comment = await client2.comment(post.id, "r")
                await client2.delete_comment(comment.id)
                await client.restore_comment(comment.id)
                await client.delete_post(post.id)

    async def test_like_comment(self):
        async with AsyncITDClient(refresh_token) as client:
            post = await client.create_post("for_test")
            comment = await client.comment(post.id, "r")
            await client.like_comment(comment.id)
            await client.like_comment(comment.id)
            await client.delete_like_comment(comment.id)
            await client.delete_like_comment(comment.id)

            await client.delete_post(post.id)

    @assert_async_raises(NotFoundError)
    async def test_like_comment_not_found(self):
        async with AsyncITDClient(refresh_token) as client:
            await client.delete_like_comment(uuid8())

    async def test_replies(self):
        async with AsyncITDClient(refresh_token) as client:
            post = await client.create_post("for_test")
            comment = await client.comment(post.id, "r")
            replay = await client.replies(comment.id, "G")
            await client.delete_post(post.id)

    async def test_replies_blank(self):
        async with AsyncITDClient(refresh_token) as client:
            post = await client.create_post("for_test")
            comment = await client.comment(post.id, "r")
            try:
                replay = await client.replies(comment.id, "")
            except ValidationError:
                pass
            await client.delete_post(post.id)

    async def test_replies_attachments_max_ken(self):
        async with AsyncITDClient(refresh_token) as client:
            post = await client.create_post("for_test")
            comment = await client.comment(post.id, "r")
            try:
                replay = await client.replies(comment.id, "", attachment_ids=[uuid8()] * 4)
            except ValidationError:
                pass
            await client.delete_post(post.id)

    async def test_replies_to_user(self):
        async with AsyncITDClient(refresh_token) as client:
            post = await client.create_post("for_test")
            comment = await client.comment(post.id, "r")
            replay = await client.replies(comment.id, "3", replay_to_user_id=uuid8())
            await client.delete_post(post.id)
