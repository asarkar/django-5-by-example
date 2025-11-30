from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from taggit.models import Tag

from ..factories import CommentFactory, PostFactory
from ..models import Comment, Post


class PostTestCase(TestCase):
    user: User
    post: Post

    @classmethod
    def setUpTestData(cls: type[PostTestCase]) -> None:
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

        now = timezone.now()
        posts = [PostFactory.create(publish=now - timedelta(days=i)) for i in range(3, 0, -1)]

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

    def test_get_absolute_url(self) -> None:
        post = PostFactory.build()

        expected_url = "/".join(
            [
                "/blog",
                str(post.publish.year),
                str(post.publish.month),
                str(post.publish.day),
                post.slug,
                "",
            ]
        )

        self.assertEqual(post.get_absolute_url(), expected_url)

    def test_slug_unique_for_day(self) -> None:
        day = timezone.now()

        post1 = PostFactory.create(
            slug="slug",
            publish=day,
        )

        post2 = PostFactory.build(
            slug=post1.slug,
            publish=post1.publish,
        )

        # Second post with SAME slug on SAME date should fail
        with self.assertRaises(ValidationError):
            post2.full_clean()

    def test_slug_can_repeat_on_different_days(self) -> None:
        day1 = timezone.now()
        post1 = PostFactory.create(
            slug="slug",
            publish=day1,
        )

        day2 = day1 - timedelta(days=1)
        post2 = PostFactory.build(
            slug=post1.slug,
            publish=day2,
            author=post1.author,  # SubFactory only runs on `create()`, not `build()`
        )

        # This should NOT raise: slug is reused on a different date
        try:
            post2.full_clean()
        except Exception as exc:
            self.fail(f"Slug incorrectly flagged as duplicate across days: {exc}")

    def test_slug_is_auto_generated_if_not_provided(self) -> None:
        post = Post.objects.create(
            title="Test Post Without Slug",
            body="Body content",
            author=self.user,
        )

        self.assertEqual(post.slug, "test-post-without-slug")

    def test_slug_not_overwritten_if_provided(self) -> None:
        post = Post.objects.create(
            title="Test Post",
            slug="custom-slug",
            body="Body content",
            author=self.user,
        )

        self.assertEqual(post.slug, "custom-slug")

    def test_slug_generation_with_special_characters(self) -> None:
        post = Post.objects.create(
            title="Post with Special!@# Characters & Symbols",
            body="Body content",
            author=self.user,
        )

        self.assertEqual(post.slug, "post-with-special-characters-symbols")

    def test_publish_date_defaults_to_now(self) -> None:
        before = timezone.now()
        post = Post.objects.create(
            title="Test Post",
            body="Body content",
            author=self.user,
        )
        after = timezone.now()

        self.assertGreaterEqual(post.publish, before)
        self.assertLessEqual(post.publish, after)

    def test_created_timestamp_auto_set(self) -> None:
        post = Post.objects.create(
            title="Test Post",
            body="Body content",
            author=self.user,
        )

        self.assertIsNotNone(post.created)
        self.assertLessEqual(post.created, timezone.now())

    def test_updated_timestamp_changes_on_save(self) -> None:
        post = PostFactory.create()

        original_updated = post.updated

        post.title = "Updated Title"
        post.save()
        post.refresh_from_db()

        self.assertGreater(post.updated, original_updated)

    def test_status_choices(self) -> None:
        self.assertEqual(Post.Status.DRAFT, "DF")
        self.assertEqual(Post.Status.PUBLISHED, "PB")
        self.assertEqual(Post.Status.DRAFT.label, "Draft")
        self.assertEqual(Post.Status.PUBLISHED.label, "Published")

    def test_default_status_is_draft(self) -> None:
        post = Post.objects.create(
            title="Test Post",
            body="Body content",
            author=self.user,
        )

        self.assertEqual(post.status, Post.Status.DRAFT)

    def test_author_foreign_key_relationship(self) -> None:
        self.assertEqual(self.post.author, self.user)
        self.assertIn(self.post, self.user.blog_posts.all())

    def test_posts_are_deleted_when_user_is_deleted(self) -> None:
        user = User.objects.create_user(username="tempuser", password="password")
        post = PostFactory.create(author=user)

        post_id = post.id
        user.delete()

        # Verify post was deleted
        with self.assertRaises(Post.DoesNotExist):
            Post.objects.get(id=post_id)

    def test_objects_manager_returns_all_posts(self) -> None:
        draft_post = PostFactory.create(status=Post.Status.DRAFT)
        published_post = PostFactory.create(status=Post.Status.PUBLISHED)

        all_posts = Post.objects.all()

        self.assertIn(draft_post, all_posts)
        self.assertIn(published_post, all_posts)

    def test_title_cannot_be_blank(self) -> None:
        post = PostFactory.build(title="")

        with self.assertRaises(ValidationError) as cm:
            post.full_clean()

        self.assertIn("title", cm.exception.message_dict)

    def test_body_cannot_be_blank(self) -> None:
        post = PostFactory.build(body="")

        with self.assertRaises(ValidationError) as cm:
            post.full_clean()

        self.assertIn("body", cm.exception.message_dict)

    def test_get_absolute_url_with_single_digit_month_and_day(self) -> None:
        local_dt = datetime(2024, 1, 5)
        post = PostFactory.build(publish=timezone.make_aware(local_dt))

        url = post.get_absolute_url()

        self.assertIn(f"/{local_dt.year}/{local_dt.month}/{local_dt.day}/", url)

    def test_tags_are_created_automatically(self) -> None:
        initial_tag_count = Tag.objects.count()

        PostFactory.create(tags=["newtag"])

        self.assertEqual(Tag.objects.count(), initial_tag_count + 1)
        self.assertTrue(Tag.objects.filter(name="newtag").exists())

    def test_tag_slugs_are_auto_generated(self) -> None:
        PostFactory.create(tags=["Django Framework"])

        tag = Tag.objects.get(name="Django Framework")
        self.assertEqual(tag.slug, "django-framework")

    def test_same_tag_can_be_used_on_multiple_posts(self) -> None:
        PostFactory.create_batch(2, tags=["python"])

        python_tag = Tag.objects.get(name="python")

        tagged_posts = Post.objects.filter(tags=python_tag)
        self.assertEqual(tagged_posts.count(), 2)

    def test_remove_tag_from_post(self) -> None:
        post = PostFactory.create(tags=["django", "python"])
        self.assertEqual(post.tags.count(), 2)

        post.tags.remove("django")

        self.assertEqual(post.tags.count(), 1)
        tag_names = list(post.tags.values_list("name", flat=True))
        self.assertEqual(tag_names, ["python"])

    def test_set_tags_replaces_existing_tags(self) -> None:
        post = PostFactory.create(tags=["django", "python"])

        post.tags.set(["java", "spring"])

        self.assertEqual(post.tags.count(), 2)
        tag_names = list(post.tags.values_list("name", flat=True))
        self.assertEqual(tag_names, ["java", "spring"])

    def test_filter_posts_by_tag(self) -> None:
        posts = PostFactory.create_batch(3)

        posts[0].tags.add("django")
        posts[1].tags.add("django")
        posts[2].tags.add("flask")

        django_posts = Post.objects.filter(tags__name="django")

        self.assertEqual(django_posts.count(), 2)
        self.assertIn(posts[0], django_posts)
        self.assertIn(posts[1], django_posts)
        self.assertNotIn(posts[2], django_posts)


class CommentTestCase(TestCase):
    post: Post

    @classmethod
    def setUpTestData(cls: type[CommentTestCase]) -> None:
        cls.post = PostFactory.create()

    def test_create_comment(self) -> None:
        comment = Comment.objects.create(
            post=self.post, name="John Doe", email="john@example.com", body="This is a test comment"
        )

        self.assertIsInstance(comment, Comment)
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.name, "John Doe")
        self.assertEqual(comment.email, "john@example.com")
        self.assertEqual(comment.body, "This is a test comment")
        # Verify default field values
        self.assertTrue(comment.active)
        self.assertIsNotNone(comment.created)
        self.assertLessEqual(comment.created, timezone.now())

    def test_comment_str(self) -> None:
        comment = CommentFactory.build(
            post=self.post, name="Jane Smith", email="jane@example.com", body="Great post!"
        )

        expected_str = f"Comment by Jane Smith on {self.post}"
        self.assertEqual(str(comment), expected_str)

    def test_updated_timestamp_changes_on_save(self) -> None:
        comment = CommentFactory.create(post=self.post)

        original_updated = comment.updated
        self.assertIsNotNone(original_updated)

        comment.body = "Updated body"
        comment.save()
        comment.refresh_from_db()

        self.assertGreaterEqual(comment.updated, original_updated)

    def test_comments_are_associated_with_post(self) -> None:
        comment1 = CommentFactory.create(post=self.post)
        comment2 = CommentFactory.create(post=self.post)

        # Test forward relationship
        self.assertEqual(comment1.post, self.post)
        self.assertEqual(comment2.post, self.post)

        # Test reverse relationship
        self.assertEqual([comment1, comment2], list(self.post.comments.all()))

    def test_comments_are_deleted_when_post_is_deleted(self) -> None:
        post = PostFactory.create()
        comment = Comment.objects.create(
            post=post, name="Test User", email="test@example.com", body="Test body"
        )

        comment_id = comment.id
        post.delete()

        with self.assertRaises(Comment.DoesNotExist):
            Comment.objects.get(id=comment_id)

    def test_posts_are_ordered_by_created_date(self) -> None:
        Comment.objects.all().delete()

        now = timezone.now()
        comments = [
            CommentFactory.create(
                post=self.post,
                created=now - timedelta(days=i),
            )
            for i in range(3, 0, -1)
        ]

        actual = list(Comment.objects.all())

        expected = sorted(comments, key=lambda c: c.created)

        self.assertEqual(actual, expected)
