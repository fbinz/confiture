from django.db import models
from django.conf import settings


class Profile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class Organization(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


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

    environment = models.ForeignKey(Environment, on_delete=models.CASCADE)

    name = models.CharField(max_length=50)
    value = models.TextField()
    type = models.PositiveSmallIntegerField(choices=ConfigItemType)
    is_secret = models.BooleanField(default=False)

    def __str__(self):
        return self.name
