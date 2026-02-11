from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = "Migrate user_type to Django groups"

    def handle(self, *args, **options):
        User = get_user_model()

        for user in User.objects.all():
            if user.user_type:
                group_name = user.get_user_type_display()
                group, _ = Group.objects.get_or_create(name=group_name)
                user.groups.add(group)

        self.stdout.write(self.style.SUCCESS("Migration completed"))
