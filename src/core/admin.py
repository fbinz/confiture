from django.contrib import admin

from .models import ConfigItem, Environment, Organization, Profile, Project, Service


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    pass


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    pass


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    pass


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    pass


@admin.register(Environment)
class EnvironmentAdmin(admin.ModelAdmin):
    pass


@admin.register(ConfigItem)
class ConfigItemAdmin(admin.ModelAdmin):
    pass
