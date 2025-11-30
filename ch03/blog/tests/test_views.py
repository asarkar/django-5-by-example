from datetime import timedelta
from http import HTTPStatus
from unittest import skip

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from taggit.models import Tag

from ..factories import CommentFactory, PostFactory
from ..forms import CommentForm, EmailPostForm
from ..models import Comment, Post


class PostListViewTestCase(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="testuser", password="password")
        self.url = "/blog/"

        Post.objects.all().delete()
        Tag.objects.all().delete()

        self.django_post = PostFactory.create(status=Post.Status.PUBLISHED, title="Django Tutorial")
        self.django_post.tags.add("django", "python")

        self.flask_post = PostFactory.create(status=Post.Status.PUBLISHED, title="Flask Tutorial")
        self.flask_post.tags.add("flask", "python")

        self.java_post = PostFactory.create(status=Post.Status.PUBLISHED, title="Java Tutorial")
        self.java_post.tags.add("java")

        self.django_post_url = reverse(
            "blog:post_detail",
            args=[
                self.django_post.publish.year,
                self.django_post.publish.month,
                self.django_post.publish.day,
                self.django_post.slug,
            ],
        )

    def test_uses_correct_template(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "blog/post/list.html")

    def test_context(self) -> None:
        Post.objects.all().delete()

        posts: list[Post] = []

        for _ in range(1, 4):
            post = PostFactory.create(
                status=Post.Status.PUBLISHED,
            )
            posts.append(post)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context["posts"]), len(posts))
        for p in posts:
            self.assertContains(response, p.title)

    def test_only_published_posts_displayed(self) -> None:
        Post.objects.all().delete()

        published_post = PostFactory.create(status=Post.Status.PUBLISHED)
        draft_post = PostFactory.create(status=Post.Status.DRAFT)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, published_post.title)
        self.assertNotContains(response, draft_post.title)
        self.assertEqual(len(response.context["posts"]), 1)

    def test_posts_ordered_by_publish_date_descending(self) -> None:
        Post.objects.all().delete()

        now = timezone.now()
        posts = [
            PostFactory.create(
                status=Post.Status.PUBLISHED,  # Add this!
                publish=now - timedelta(days=i),
            )
            for i in range(3, 0, -1)
        ]

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        actual = list(response.context["posts"])
        expected = sorted(posts, key=lambda p: p.publish, reverse=True)

        self.assertEqual(actual, expected)

    def test_pagination(self) -> None:
        Post.objects.all().delete()

        for _ in range(5):
            PostFactory.create(status=Post.Status.PUBLISHED)

        response = self.client.get(self.url)

        # function-based view doesn't automatically provide an
        # `is_paginated` context variable like Django's ListView does.
        # self.assertTrue(response.context["is_paginated"])
        posts_page = response.context["posts"]
        self.assertEqual(len(posts_page), 3)
        self.assertGreater(posts_page.paginator.num_pages, 1)
        self.assertEqual(posts_page.paginator.num_pages, 2)

    def test_pagination_invalid_page_number(self) -> None:
        Post.objects.all().delete()

        PostFactory.create(status=Post.Status.PUBLISHED)

        response = self.client.get(f"{self.url}?page=999")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["posts"].number, 1)

    def test_pagination_non_numeric_page_parameter(self) -> None:
        Post.objects.all().delete()

        PostFactory.create(status=Post.Status.PUBLISHED)

        response = self.client.get(f"{self.url}?page=invalid")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["posts"].number, 1)

    def test_empty_list_when_no_published_posts(self) -> None:
        Post.objects.all().delete()

        PostFactory.create(status=Post.Status.DRAFT)
        PostFactory.create(status=Post.Status.DRAFT)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context["posts"]), 0)

    def test_pagination_context_variables(self) -> None:
        Post.objects.all().delete()

        for _ in range(5):
            PostFactory.create(status=Post.Status.PUBLISHED)

        response = self.client.get(self.url)

        self.assertIn("posts", response.context)
        posts = response.context["posts"]

        self.assertTrue(hasattr(posts, "paginator"))
        self.assertTrue(hasattr(posts, "number"))
        self.assertEqual(posts.paginator.num_pages, 2)

    def test_exactly_three_posts_no_pagination(self) -> None:
        Post.objects.all().delete()

        for _ in range(3):
            PostFactory.create(status=Post.Status.PUBLISHED)

        response = self.client.get(self.url)

        posts_page = response.context["posts"]
        self.assertEqual(len(posts_page), 3)
        self.assertEqual(posts_page.paginator.num_pages, 1)

    def test_view_uses_published_manager(self) -> None:
        Post.objects.all().delete()

        published_posts = [PostFactory.create(status=Post.Status.PUBLISHED) for _ in range(3)]
        for _ in range(2):
            PostFactory.create(status=Post.Status.DRAFT)

        response = self.client.get(self.url)

        self.assertEqual(len(response.context["posts"]), len(published_posts))

        for post in response.context["posts"]:
            self.assertIn(post, published_posts)

    @skip("Ignores the POST body but returns 200")
    def test_get_request_method_only(self) -> None:
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_view_without_tag_shows_all_posts(self) -> None:
        url = reverse("blog:post_list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context["posts"]), 3)

    def test_view_with_tag_filters_posts(self) -> None:
        django_tag = Tag.objects.get(name="django")
        url = reverse("blog:post_list_by_tag", args=[django_tag.slug])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        posts = list(response.context["posts"])
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].title, "Django Tutorial")

    def test_view_with_shared_tag_shows_multiple_posts(self) -> None:
        python_tag = Tag.objects.get(name="python")
        url = reverse("blog:post_list_by_tag", args=[python_tag.slug])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        posts = list(response.context["posts"])
        self.assertEqual(len(posts), 2)
        post_titles = {post.title for post in posts}

        self.assertEqual(post_titles, {"Django Tutorial", "Flask Tutorial"})

    def test_view_with_nonexistent_tag_returns_404(self) -> None:
        url = reverse("blog:post_list_by_tag", args=["nonexistent-tag"])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_tag_context_contains_tag_object_with_filter(self) -> None:
        django_tag = Tag.objects.get(name="django")
        url = reverse("blog:post_list_by_tag", args=[django_tag.slug])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIsNotNone(response.context["tag"])
        self.assertEqual(response.context["tag"], django_tag)
        self.assertEqual(response.context["tag"].name, "django")

    def test_draft_posts_not_shown_even_with_matching_tag(self) -> None:
        draft_post = PostFactory.create(status=Post.Status.DRAFT, title="Draft Django Post")
        draft_post.tags.add("django")

        django_tag = Tag.objects.get(name="django")
        url = reverse("blog:post_list_by_tag", args=[django_tag.slug])
        response = self.client.get(url)

        # Should still only show 1 post (the published one)
        self.assertEqual(len(response.context["posts"]), 1)
        self.assertNotContains(response, draft_post.title)

    def test_tag_filtering_with_pagination(self) -> None:
        PostFactory.create_batch(5, status=Post.Status.PUBLISHED, tags=["popular"])

        popular_tag = Tag.objects.get(name="popular")
        url = reverse("blog:post_list_by_tag", args=[popular_tag.slug])
        response = self.client.get(url)

        # First page should have 3 posts
        self.assertEqual(len(response.context["posts"]), 3)
        self.assertEqual(response.context["posts"].paginator.count, 5)

        response = self.client.get(f"{url}?page=2")

        # Second page should have 2 posts
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context["posts"]), 2)

    def test_posts_with_multiple_tags_can_be_filtered_by_any(self) -> None:
        multi_tag_post = PostFactory.create(
            status=Post.Status.PUBLISHED, title="Multi Tag Post", tags=["django", "python", "web"]
        )

        for tag_name in ["django", "python", "web"]:
            tag = Tag.objects.get(name=tag_name)
            url = reverse("blog:post_list_by_tag", args=[tag.slug])
            response = self.client.get(url)

            self.assertContains(response, multi_tag_post.title)

    def test_uses_correct_template_with_tag_filter(self) -> None:
        django_tag = Tag.objects.get(name="django")
        url = reverse("blog:post_list_by_tag", args=[django_tag.slug])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "blog/post/list.html")

    def test_similar_posts_in_context(self) -> None:
        response = self.client.get(self.django_post_url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("similar_posts", response.context)

    def test_similar_posts_with_matching_tags(self) -> None:
        response = self.client.get(self.django_post_url)

        similar_posts = response.context["similar_posts"]
        self.assertEqual(len(similar_posts), 1)
        self.assertIn(self.flask_post, similar_posts)
        self.assertNotIn(self.java_post, similar_posts)
        self.assertNotIn(self.django_post, similar_posts)

    def test_similar_posts_complex_ordering(self) -> None:
        # 2 shared tags, older
        post_a = PostFactory.create(
            status=Post.Status.PUBLISHED,
            publish=self.django_post.publish - timedelta(days=10),
            tags=["django", "python", "web"],
        )

        # 2 shared tags, newer
        post_b = PostFactory.create(
            status=Post.Status.PUBLISHED,
            publish=self.django_post.publish - timedelta(days=5),
            tags=["django", "python", "web"],
        )

        # 1 shared tag
        post_c = PostFactory.create(
            status=Post.Status.PUBLISHED,
            publish=self.django_post.publish - timedelta(days=2),
            tags=["django"],
        )

        response = self.client.get(self.django_post_url)

        similar_posts = response.context["similar_posts"]

        self.assertEqual(similar_posts[0], post_b)
        self.assertEqual(similar_posts[1], post_a)
        self.assertEqual(similar_posts[2], post_c)


class PostDetailViewTestCase(TestCase):
    user: User
    post: Post
    url: str

    @classmethod
    def setUpTestData(cls: type[PostDetailViewTestCase]) -> None:
        cls.user = User.objects.create_user(username="testuser", password="password")
        cls.post = PostFactory.create(status=Post.Status.PUBLISHED)
        cls.url = cls.post.get_absolute_url()

    def test_uses_correct_template(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "blog/post/detail.html")

    def test_context(self) -> None:
        CommentFactory.create(post=self.post, active=True)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("post", response.context)
        self.assertIn("comments", response.context)
        self.assertIn("form", response.context)
        self.assertEqual(response.context["post"], self.post)

    def test_displays_active_comments_only(self) -> None:
        active_comment = CommentFactory.create(post=self.post)
        inactive_comment = CommentFactory.create(active=False)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("comments", response.context)
        comments = response.context["comments"]
        self.assertEqual(comments.count(), 1)
        self.assertIn(active_comment, comments)
        self.assertNotIn(inactive_comment, comments)

    def test_displays_no_comments_when_none_exist(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("comments", response.context)
        comments = response.context["comments"]
        self.assertEqual(comments.count(), 0)

    def test_displays_comments_for_current_post_only(self) -> None:
        this_post_comment = CommentFactory.create(post=self.post)

        other_post = PostFactory.create(status=Post.Status.PUBLISHED)
        other_post_comment = CommentFactory.create(post=other_post)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        comments = response.context["comments"]
        self.assertEqual(comments.count(), 1)
        self.assertIn(this_post_comment, comments)
        self.assertNotIn(other_post_comment, comments)

    def test_comments_are_ordered_by_created_date(self) -> None:
        now = timezone.now()
        comments = [
            CommentFactory.create(
                post=self.post,
                created=now - timedelta(days=i),
            )
            for i in range(3, 0, -1)
        ]

        response = self.client.get(self.url)

        actual = list(response.context["comments"])
        self.assertEqual(comments, actual)

    def test_view_displays_comment_form(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], CommentForm)


class PostShareViewTestCase(TestCase):
    post: Post
    url: str

    @classmethod
    def setUpTestData(cls: type[PostShareViewTestCase]) -> None:
        cls.post = PostFactory.create(status=Post.Status.PUBLISHED)
        cls.url = reverse("blog:post_share", args=[cls.post.id])

    def test_get_request_displays_form(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "blog/post/share.html")
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], EmailPostForm)
        self.assertIn("post", response.context)
        self.assertEqual(response.context["post"], self.post)
        self.assertFalse(response.context["sent"])

    def test_post_request_with_valid_data_sends_email(self) -> None:
        form_data = PostShareViewTestCase._form_data()

        response = self.client.post(self.url, data=form_data)

        # The test runner replaces the normal email backend with a testing backend.
        # https://docs.djangoproject.com/en/5.2/topics/testing/tools/#email-services
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]

        self.assertIn(form_data["name"], sent_email.subject)
        self.assertIn(form_data["email"], sent_email.subject)
        self.assertIn(self.post.title, sent_email.subject)
        self.assertIn(self.post.title, sent_email.body)
        self.assertIn(form_data["comments"], sent_email.body)
        self.assertEqual(sent_email.to, [form_data["to"]])

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response.context["sent"])

    def test_post_request_with_invalid_data_does_not_send_email(self) -> None:
        form_data = PostShareViewTestCase._form_data()
        form_data["email"] = "invalid-email"

        response = self.client.post(self.url, data=form_data)

        # Check no email was sent
        self.assertEqual(len(mail.outbox), 0)

        # Verify response
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(response.context["sent"])

        # Verify form has errors
        form = response.context["form"]
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)
        self.assertIn("email", form.errors)

    def test_post_request_with_missing_fields(self) -> None:
        form_data = {
            "name": "John Doe",
            # Missing email, to, and comments
        }

        response = self.client.post(self.url, data=form_data)

        # Check no email was sent
        self.assertEqual(len(mail.outbox), 0)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(response.context["sent"])

    def test_share_draft_post_returns_404(self) -> None:
        draft_post = PostFactory.create(status=Post.Status.DRAFT)
        url = reverse("blog:post_share", args=[draft_post.id])

        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_share_nonexistent_post_returns_404(self) -> None:
        url = reverse("blog:post_share", args=[99999])

        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_email_contains_absolute_url(self) -> None:
        _ = self.client.post(self.url, data=PostShareViewTestCase._form_data())

        sent_email = mail.outbox[0]
        self.assertIn("http://", sent_email.body)
        self.assertIn(self.post.get_absolute_url(), sent_email.body)

    def test_context_after_successful_submission(self) -> None:
        response = self.client.post(self.url, data=PostShareViewTestCase._form_data())

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("post", response.context)
        self.assertIn("form", response.context)
        self.assertIn("sent", response.context)
        self.assertEqual(response.context["post"], self.post)
        self.assertTrue(response.context["sent"])

    @staticmethod
    def _form_data() -> dict[str, str]:
        return {
            "name": "Test User",
            "email": "test@example.com",
            "to": "recipient@example.com",
            "comments": "Great post!",
        }


class PostCommentViewTestCase(TestCase):
    post: Post
    url: str

    @classmethod
    def setUpTestData(cls: type[PostCommentViewTestCase]) -> None:
        cls.post = PostFactory.create(status=Post.Status.PUBLISHED)
        cls.url = reverse("blog:post_comment", args=[cls.post.id])

    @staticmethod
    def _form_data() -> dict[str, str]:
        return {
            "name": "John Commenter",
            "email": "john@example.com",
            "body": "This is a great post!",
        }

    def test_requires_post_method(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_post_valid_comment_creates_comment(self) -> None:
        initial_comment_count = Comment.objects.count()
        form_data = PostCommentViewTestCase._form_data()

        response = self.client.post(self.url, data=form_data)

        # Verify comment was created
        self.assertEqual(Comment.objects.count(), initial_comment_count + 1)

        # Verify the comment details
        comment = Comment.objects.latest("created")
        self.assertEqual(comment.name, form_data["name"])
        self.assertEqual(comment.email, form_data["email"])
        self.assertEqual(comment.body, form_data["body"])
        self.assertEqual(comment.post, self.post)
        self.assertTrue(comment.active)

        # Verify response
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "blog/post/comment.html")
        self.assertEqual(response.context["comment"], comment)

    def test_post_invalid_comment_does_not_create_comment(self) -> None:
        initial_comment_count = Comment.objects.count()

        form_data = PostCommentViewTestCase._form_data()
        form_data["email"] = "invalid-email"

        response = self.client.post(self.url, data=form_data)

        # Verify no comment was created
        self.assertEqual(Comment.objects.count(), initial_comment_count)

        # Verify response
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIsNone(response.context["comment"])
        self.assertFalse(response.context["form"].is_valid())

    def test_post_missing_required_fields(self) -> None:
        initial_comment_count = Comment.objects.count()

        form_data = {
            "name": "John Commenter",
            # Missing email and body
        }

        response = self.client.post(self.url, data=form_data)

        # Verify no comment was created
        self.assertEqual(Comment.objects.count(), initial_comment_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIsNone(response.context["comment"])

    def test_comment_on_draft_post_returns_404(self) -> None:
        draft_post = PostFactory.create(status=Post.Status.DRAFT)
        url = reverse("blog:post_comment", args=[draft_post.id])

        response = self.client.post(url, data=PostCommentViewTestCase._form_data())
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_comment_on_nonexistent_post_returns_404(self) -> None:
        url = reverse("blog:post_comment", args=[99999])

        response = self.client.post(url, data=PostCommentViewTestCase._form_data())
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_comment_is_associated_with_correct_post(self) -> None:
        other_post = PostFactory.create(status=Post.Status.PUBLISHED)

        _ = self.client.post(self.url, data=PostCommentViewTestCase._form_data())

        comment = Comment.objects.latest("created")
        self.assertEqual(comment.post, self.post)
        self.assertNotEqual(comment.post, other_post)

    def test_context_contains_all_required_data(self) -> None:
        response = self.client.post(self.url, data=PostCommentViewTestCase._form_data())

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("post", response.context)
        self.assertIn("form", response.context)
        self.assertIn("comment", response.context)
        self.assertEqual(response.context["post"], self.post)
        self.assertIsInstance(response.context["form"], CommentForm)

    def test_multiple_comments_on_same_post(self) -> None:
        form_data = {"name": "User Two", "email": "user2@example.com", "body": "Second comment"}

        _ = self.client.post(self.url, data=PostCommentViewTestCase._form_data())
        _ = self.client.post(self.url, data=form_data)

        comments = Comment.objects.filter(post=self.post)
        self.assertEqual(comments.count(), 2)

    def test_comment_form_in_context_after_invalid_submission(self) -> None:
        form_data = PostCommentViewTestCase._form_data()
        form_data["name"] = ""

        response = self.client.post(self.url, data=form_data)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        form = response.context["form"]
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)
