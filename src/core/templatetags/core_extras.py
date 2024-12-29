from django import template
from django.shortcuts import reverse

from core.models import ConfigItemValue, Environment, Organization, Project, Service

register = template.Library()


@register.filter
def times(x, y):
    print(x, y)
    return x * y


@register.filter
def nav_url(target):
    if isinstance(target, Organization):
        return reverse(
            "core:org-detail",
            args=(target.id,),
        )
    if isinstance(target, Project):
        return reverse(
            "core:project-detail",
            args=(
                target.organization.id,
                target.id,
            ),
        )
    if isinstance(target, Service):
        return reverse(
            "core:service-detail",
            args=(
                target.project.organization.id,
                target.project.id,
                target.id,
            ),
        )
    if isinstance(target, Environment):
        return reverse(
            "core:environment-detail",
            args=(
                target.service.project.organization.id,
                target.service.project.id,
                target.service.id,
                target.id,
            ),
        )

    raise ValueError("Unknown nav target", target)


@register.filter
def nav_label(target):
    if isinstance(target, (Organization, Service, Project, Environment)):
        return target.name

    raise ValueError("Unknown nav target", target)


@register.filter
def get_for_env(values: list[ConfigItemValue], env: Environment):
    for value in values:
        if not value:
            continue

        if value.environment == env:
            return value
