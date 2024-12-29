import django_magic_context as magic
from django.db.models import Count, OuterRef, Subquery
from django.template.response import TemplateResponse

from core.models import Organization, Project, Service


def get_org(org_id):
    return Organization.objects.get(id=org_id)


def get_projects(org_id):
    projects = Project.objects.filter(organization_id=org_id).annotate(
        num_services=Subquery(
            Service.objects.filter(project_id=OuterRef("id"))
            .values("project_id")
            .annotate(count=Count("id"))
            .values("count")
        )
    )
    return projects


def view(request, org_id: str):
    context = magic.resolve(
        org_id=org_id,
        org=get_org,
        projects=get_projects,
    )

    return TemplateResponse(request, "core/org_index.html", context)
