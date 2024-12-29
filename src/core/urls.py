from django.urls import path, include, register_converter
from sqids import Sqids

from core.views import index
from core.views.environment import index as environment_index
from core.views.org import index as org_index
from core.views.project import index as project_index
from core.views.service import index as service_index


class SqidConverter:
    prefix = "id-"
    alphabet = "abcdefghkmnopqrstuvwxyz23456789"

    def __init__(self):
        self.sqids = Sqids(alphabet=self.alphabet, min_length=4)
        self.regex = f"{self.prefix}[a-zA-Z0-9]*"

    def to_python(self, value):
        value = value.removeprefix(self.prefix)
        decoded_value, *rest = self.sqids.decode(value)
        if rest:
            raise ValueError()

        return decoded_value

    def to_url(self, value):
        encoded_value = self.sqids.encode([int(value)])
        return f"{self.prefix}{encoded_value}"


class OrgIdConverter(SqidConverter):
    prefix = "o-"


class ProjectIdConverter(SqidConverter):
    prefix = "p-"


class ServiceIdConverter(SqidConverter):
    prefix = "s-"


class EnvironmentIdConverter(SqidConverter):
    prefix = "e-"


register_converter(SqidConverter, "sqid")
register_converter(OrgIdConverter, "org-id")
register_converter(ProjectIdConverter, "project-id")
register_converter(ServiceIdConverter, "service-id")
register_converter(EnvironmentIdConverter, "environment-id")


app_name = "core"
urlpatterns = [
    path("o/", index.view, name="index"),
    path(
        "o/<org-id:org_id>/",
        org_index.view,
        name="org-detail",
    ),
    path(
        "o/<org-id:org_id>/p/<project-id:project_id>/",
        project_index.view,
        name="project-detail",
    ),
    path(
        "o/<org-id:org_id>/p/<project-id:project_id>/s/<service-id:service_id>/",
        include(
            [
                path("", service_index.view, name="service-detail"),
                path(
                    "items/",
                    service_index.view,
                    name="service-item-list",
                    kwargs=dict(resource="items", action="new"),
                ),
                path(
                    "items/new",
                    service_index.view,
                    name="service-item-new",
                    kwargs=dict(resource="items", action="new"),
                ),
                path(
                    "items/<int:item_id>/view/",
                    service_index.view,
                    name="service-item-view",
                    kwargs=dict(resource="items", action="view"),
                ),
                path(
                    "items/<int:item_id>/edit/",
                    service_index.view,
                    name="service-item-edit",
                    kwargs=dict(resource="items", action="edit"),
                ),
                path(
                    "items/<int:item_id>/env/<int:env_id>/edit/",
                    service_index.view,
                    name="service-value-edit",
                    kwargs=dict(resource="values", action="edit"),
                ),
                path(
                    "items/<int:item_id>/env/<int:env_id>/view/",
                    service_index.view,
                    name="service-value-view",
                    kwargs=dict(resource="values", action="view"),
                ),
            ]
        ),
    ),
    path(
        "o/<org-id:org_id>/p/<project-id:project_id>/s/<service-id:service_id>/e/<environment-id:environment_id>/",
        environment_index.view,
        name="environment-detail",
    ),
]
