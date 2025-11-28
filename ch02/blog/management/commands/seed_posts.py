from typing import Any

from django.contrib.auth import get_user_model
from django.core.management import CommandParser
from django.core.management.base import BaseCommand

from ...factories import PostFactory

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Seed the database with random blog posts.\n\n"
        "Usage:\n"
        "  python manage.py seed_posts [--count N]\n\n"
        "Options:\n"
        "  --count N    Number of posts to create (default: 10)\n\n"
        "Example:\n"
        "  python manage.py seed_posts --count 50"
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--count",
            type=int,
            default=10,
            help="Number of posts to create (default: 10)",
        )

    def handle(self, *args: Any, **kwargs: Any) -> None:
        count = kwargs["count"]

        # Ensure there are users to assign posts to
        users = User.objects.all()
        if not users.exists():
            self.stdout.write(
                self.style.ERROR("No users found! Run 'python manage.py seed_users' first.")
            )
            return

        # Create posts
        PostFactory.create_batch(count)

        self.stdout.write(self.style.SUCCESS(f"Successfully created {count} posts!"))
