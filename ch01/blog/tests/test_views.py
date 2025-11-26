from typing import Any

from django.contrib.auth.models import User
from django.test import TestCase

from ..models import Post


class TestPostListView(TestCase):
    user: User

    @classmethod
    def setUpTestData(cls: type[TestPostListView]) -> None:
        cls.user = User.objects.create_user(username="testuser", password="password")

    def test_uses_correct_template(self) -> None:
        response = self.client.get("/blog/")
        self.assertTemplateUsed(response, "blog/post/list.html")

    def test_context(self) -> None:
        Post.objects.all().delete()

        posts: list[Post] = []

        for i in range(1, 4):
            post = Post.objects.create(
                title=f"Post {i}",
                body=f"Body {i}",
                author=self.user,
                # Only published posts are listed
                status=Post.Status.PUBLISHED,
            )
            posts.append(post)

        response = self.client.get("/blog/")
        self.assertEqual(len(response.context["posts"]), len(posts))
        for p in posts:
            self.assertContains(response, p.title)


class TestPostDetailView(TestCase):
    user: User

    @classmethod
    def setUpTestData(cls: type[TestPostDetailView]) -> None:
        cls.user = User.objects.create_user(username="testuser", password="password")

    def test_uses_correct_template(self) -> None:
        post = Post.objects.create(**self._post_fields())

        response = self.client.get(f"/blog/{post.id}/")
        self.assertTemplateUsed(response, "blog/post/detail.html")

    def _post_fields(self) -> dict[str, Any]:
        return {
            "title": "Post",
            "body": "Body",
            "author": self.user,
            # Only published posts are listed
            "status": Post.Status.PUBLISHED,
        }

    def test_context(self) -> None:
        Post.objects.all().delete()

        post = Post.objects.create(**self._post_fields())

        response = self.client.get(f"/blog/{post.id}/")
        self.assertEqual(response.context["post"], post)
        self.assertContains(response, post.title)
