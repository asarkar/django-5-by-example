from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from factory import post_generation  # type: ignore[attr-defined]
from factory.declarations import Iterator, LazyAttribute, SubFactory
from factory.django import DjangoModelFactory
from factory.faker import Faker

from .models import Comment, Post

# mypy: disable-error-code="no-untyped-call"

User = get_user_model()


class UserFactory(DjangoModelFactory[User]):  # type: ignore[valid-type]
    class Meta:
        model = User

    username = Faker("user_name")
    email = Faker("email")


class PostFactory(DjangoModelFactory[Post]):
    class Meta:
        model = Post

    title = Faker("sentence", nb_words=6)
    body = Faker("paragraph", nb_sentences=5)
    author = SubFactory(UserFactory)
    status = Iterator([Post.Status.DRAFT, Post.Status.PUBLISHED])
    publish = Faker(
        "date_time_this_year",
        before_now=True,
        after_now=False,
        tzinfo=timezone.get_current_timezone(),
    )
    created = LazyAttribute(lambda obj: obj.publish)
    updated = LazyAttribute(lambda obj: obj.publish)
    slug = LazyAttribute(lambda obj: slugify(str(obj.title)))

    # tags work differently - they're added via a manager
    # after the object is saved, not set as a field value.
    @post_generation  # type: ignore[misc]
    def tags(self, create: bool, extracted: list[str] | tuple[str, ...] | None) -> None:
        if not create or extracted is None:
            return

        if not isinstance(extracted, (list, tuple)):
            raise TypeError(f"tags must be a list or tuple, got {type(extracted).__name__}")

        self.tags.add(*extracted)

    # Optional: helper to get a real datetime with timezone
    @staticmethod
    def now() -> datetime:
        return timezone.now()


class CommentFactory(DjangoModelFactory[Comment]):
    class Meta:
        model = Comment

    post = SubFactory(PostFactory)
    name = Faker("name")
    email = Faker("email")
    body = Faker("paragraph", nb_sentences=5)
    active = True
