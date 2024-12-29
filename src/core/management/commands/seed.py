from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand

from core.models import (
    ConfigItem,
    ConfigItemValue,
    Environment,
    Organization,
    Profile,
    Project,
    Service,
)


class Command(BaseCommand):
    help = "Seed the database."

    def handle(self, *args, **options):
        User = get_user_model()
        call_command("flush", interactive=False)

        user = User.objects.create_superuser(
            username="admin",
            email="",
            password="Admin123$",
        )

        org_1 = Organization.objects.create(
            name="Example Org",
        )

        org_2 = Organization.objects.create(
            name="No Projects Org",
        )

        Profile.objects.create(organization=org_1, user=user)
        Profile.objects.create(organization=org_2, user=user)

        project_1 = Project.objects.create(
            name="Example Project 1",
            organization=org_1,
        )

        Project.objects.create(
            name="Example Project 2",
            organization=org_1,
        )

        service = Service.objects.create(
            name="Example Service",
            project=project_1,
        )

        item = ConfigItem.objects.create(
            service=service,
            name="EXAMPLE",
            type=ConfigItem.Type.ENV,
        )

        for name in ("test", "prod"):
            environment = Environment.objects.create(
                name=name,
                service=service,
            )

            ConfigItemValue.objects.create(
                item=item,
                environment=environment,
                value="VALUE",
            )
