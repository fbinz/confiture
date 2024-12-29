from django.conf import settings
from django.db import models


class AdapterConfig(models.Model):
    cls = models.CharField(max_length=255, help_text="Dotted path of adapter class")
    config = models.JSONField()


class Organization(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)


class Project(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Service(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Environment(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)

    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class ConfigItemType(models.IntegerChoices):
    ENV = 1
    FILE = 2
    REF = 3


class ConfigItem(models.Model):
    Type = ConfigItemType

    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    type = models.PositiveSmallIntegerField(choices=ConfigItemType)
    is_secret = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class ConfigItemValue(models.Model):
    item = models.ForeignKey(ConfigItem, on_delete=models.CASCADE)
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE)

    value = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["item", "environment"],
                name="unique_item_per_environment",
            ),
        ]

    def __str__(self):
        return self.value
