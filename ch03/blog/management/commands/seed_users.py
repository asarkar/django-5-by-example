from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Create default users."

    def handle(self, *args: Any, **kwargs: Any) -> None:
        # Create superuser if not exists
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username="admin", email="admin@example.com", password="admin"
            )
            self.stdout.write(self.style.SUCCESS("Created superuser: admin"))
        else:
            self.stdout.write(self.style.NOTICE("Superuser already exists"))

        # Create regular user if not exists
        if not User.objects.filter(is_superuser=False).exists():
            User.objects.create_user(username="user", email="user@example.com", password="user")
            self.stdout.write(self.style.SUCCESS("Created regular user: user"))
        else:
            self.stdout.write(self.style.NOTICE("Regular user already exists"))
