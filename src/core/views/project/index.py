import django_magic_context as magic
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse

from core.models import Project, Service


def get_services(org_id, project_id):
    return Service.objects.filter(
        project_id=project_id,
        project__organization_id=org_id,
    )


def view(request, org_id, project_id):
    project = get_object_or_404(
        Project.objects.select_related("organization"),
        id=project_id,
        organization_id=org_id,
    )

    context = magic.resolve(
        org_id=org_id,
        project_id=project_id,
        org=project.organization,
        project=project,
        services=get_services,
    )

    return TemplateResponse(request, "core/project_index.html", context)
