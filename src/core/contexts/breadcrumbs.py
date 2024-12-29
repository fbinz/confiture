from django.db.models import Q

from core.models import Organization, Profile, Project, Service


def get_breadcrumbs(user, org_id=None, project_id=None, service_id=None):
    profiles = Profile.objects.filter(user=user)
    breadcrumbs = []

    orgs = (
        Organization.objects.filter(id__in=profiles.values("organization_id"))
        .annotate(is_current=Q(id=org_id))
        .order_by("name")
    )
    breadcrumbs.append(orgs)

    if project_id:
        projects = (
            Project.objects.filter(organization__in=orgs)
            .annotate(is_current=Q(id=project_id))
            .order_by("name")
        )
        breadcrumbs.append(projects)

    if service_id:
        services = (
            Service.objects.filter(project__in=projects)
            .annotate(is_current=Q(id=service_id))
            .order_by("name")
        )
        breadcrumbs.append(services)

    return breadcrumbs
