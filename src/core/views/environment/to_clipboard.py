from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404

from core.models import Environment


def view(request, org_id, project_id, service_id, environment_id):
    env = get_object_or_404(
        Environment,
        id=environment_id,
        service_id=service_id,
        service__project_id=project_id,
        service__project__organization_id=org_id,
    )

    print(env)

    return HttpResponse()
