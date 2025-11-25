from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from ..models import Post


class TestPostModel(TestCase):
    user: User
    post: Post

    @classmethod
    def setUpTestData(cls: type[TestPostModel]) -> None:
        cls.user = User.objects.create_user(username="testuser", password="password")

        cls.post = Post.objects.create(
            title="My blog post",
            body="This is my first post",
            author=cls.user,
        )

    def test_create_post(self) -> None:
        self.assertEqual(self.post.title, "My blog post")
        self.assertEqual(self.post.slug, "my-blog-post")
        self.assertEqual(self.post.author, self.user)
        self.assertEqual(self.post.status, Post.Status.DRAFT)

    def test_post_str(self) -> None:
        self.assertEqual(str(self.post), "My blog post")

    def test_slugs_are_not_unique(self) -> None:
        second_title = Post.objects.create(
            title=self.post.title,
            body=self.post.body,
            author=self.user,
        )

        self.assertEqual(self.post.slug, second_title.slug)

    def test_posts_are_ordered_by_publish_date(self) -> None:
        Post.objects.all().delete()

        posts: list[Post] = []
        now = timezone.now()

        for i in range(1, 4):
            post = Post.objects.create(
                title=f"Post {i}",
                body=f"Body {i}",
                author=self.user,
                publish=now - timedelta(days=1),
            )
            posts.append(post)

        actual = list(Post.objects.all())

        # Expected order is descending by publish
        expected = sorted(posts, key=lambda p: p.publish, reverse=True)

        self.assertEqual(actual, expected)

    def test_published_manager_returns_only_published(self) -> None:
        Post.objects.create(
            title="My blog post 2",
            body="This is my second post",
            author=self.user,
            status=Post.Status.PUBLISHED,
        )

        published_posts = Post.published.all()

        self.assertEqual(published_posts.count(), 1)
        self.assertEqual(published_posts[0].title, "My blog post 2")
