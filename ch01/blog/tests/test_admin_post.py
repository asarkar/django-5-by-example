from http import HTTPStatus

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from ..models import Post


class TestPostAdminFunctional(TestCase):
    admin_user: User
    user: User
    post1: Post
    post2: Post
    post3: Post

    # -----------------------------
    # Test data setup
    # -----------------------------
    @classmethod
    def setUpTestData(cls) -> None:
        # Superuser for admin
        cls.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password",
        )
        # Regular user for posts
        cls.user = User.objects.create_user(
            username="testuser",
            email="user@example.com",
            password="password",
        )

        # Create posts with different status and publish dates
        cls.post1 = Post.objects.create(
            title="First Post",
            slug="first-post",
            body="Content",
            author=cls.user,
            status=Post.Status.PUBLISHED,
            publish="2025-01-02T10:00:00Z",
        )
        cls.post2 = Post.objects.create(
            title="Second Post",
            slug="second-post",
            body="More content",
            author=cls.user,
            status=Post.Status.DRAFT,
            publish="2025-01-01T10:00:00Z",
        )
        cls.post3 = Post.objects.create(
            title="Third Post",
            slug="third-post",
            body="Extra content",
            author=cls.user,
            status=Post.Status.PUBLISHED,
            publish="2025-01-01T12:00:00Z",
        )

    # -----------------------------
    # Setup client login
    # -----------------------------
    def setUp(self) -> None:
        self.client.login(username="admin", password="password")

    # -----------------------------
    # Admin list page ordering
    # -----------------------------
    def test_admin_post_ordering(self) -> None:
        url = reverse("admin:blog_post_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        qs = list(response.context["cl"].queryset)

        expected_order = sorted(
            [self.post1, self.post2, self.post3], key=lambda p: (p.status, p.publish)
        )

        self.assertEqual(qs, expected_order)

    # -----------------------------
    # Admin search functionality
    # -----------------------------
    def test_admin_search(self) -> None:
        url = reverse("admin:blog_post_changelist") + "?q=First"
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, self.post1.title)
        self.assertNotContains(response, self.post2.title)
        self.assertNotContains(response, self.post3.title)

    # -----------------------------
    # Raw ID fields lookup
    # -----------------------------
    def test_admin_raw_id_fields_lookup(self) -> None:
        url = reverse("admin:blog_post_add")
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # The author field should use raw ID widget
        self.assertContains(response, "id_author")  # input element
        self.assertContains(response, "related-lookup")  # JS for raw_id_fields

    # -----------------------------
    # Prepopulated fields
    # -----------------------------
    def test_admin_prepopulated_fields(self) -> None:
        url = reverse("admin:blog_post_add")
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Check that prepopulate JS is included
        self.assertContains(response, "prepopulate")
