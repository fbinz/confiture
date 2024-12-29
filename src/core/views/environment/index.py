from typing import Callable

import django_magic_context as magic
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _

from core.models import ConfigItem, Environment
from core.types import ConfigTable


def get_config_table(environment) -> ConfigTable:
    rows = ConfigItem.objects.filter(environment=environment)
    return ConfigTable(headers=[_("Name"), _("Value")], rows=rows)


def get_config_table_row_form(item_id):
    item = get_object_or_404(ConfigItem, id=item_id)
    return ConfigTableRowForm(id=item_id, instance=item)


def get_config_table_row_item(item_id):
    item = get_object_or_404(ConfigItem, id=item_id)
    return item


def hx_target(request, test: Callable[[str], bool]) -> bool:
    header = request.headers.get("HX-Target")
    if not header:
        return False

    return test(header)


def handle_save(request, item_id, environment):
    form = ConfigTableRowForm(
        request.POST,
        id=item_id,
        instance=ConfigItem.objects.filter(id=item_id, environment=environment).first(),
    )
    if form.is_valid():
        item = form.save(commit=False)
        item.type = ConfigItem.Type.ENV
        item.environment = environment
        item.save()
        item_id = item.id

    return item_id


def handle_delete(request, item_id):
    ConfigItem.objects.filter(id=item_id).delete()
    return HttpResponse(status=200)


def handle_clipboard(request, *, format, environment):
    items = ConfigItem.objects.filter(environment=environment).order_by("name")
    if format == "env":
        content = "\n".join(f"{item.name}={item.value}" for item in items)
    elif format == "envrc":
        content = "\n".join(f"export {item.name}={item.value}" for item in items)
    else:
        raise HttpResponse(status=400)

    return HttpResponse(content)


def view(request, org_id, project_id, service_id, environment_id):
    environment = get_object_or_404(
        Environment.objects.select_related(
            "service",
            "service__project",
            "service__project__organization",
        ),
        id=environment_id,
        service_id=service_id,
        service__project_id=project_id,
        service__project__organization_id=org_id,
    )

    item_id = request.GET.get("item")

    action = request.GET.get("action") or request.POST.get("action")
    method = request.method

    if action == "save" and method == "POST":
        item_id = handle_save(request, item_id, environment)
    elif action == "delete" and item_id:
        return handle_delete(request, item_id)
    elif action == "clipboard-env":
        return handle_clipboard(request, environment=environment, format="env")
    elif action == "clipboard-envrc":
        return handle_clipboard(request, environment=environment, format="envrc")

    context = magic.resolve(
        environment=environment,
        service=environment.service,
        project=environment.service.project,
        organization=environment.service.project.organization,
        config_table_row_empty_form=ConfigTableRowForm(id=item_id),
        item_id=item_id,
        config_table=get_config_table,
        config_table_row_form=get_config_table_row_form,
        config_table_row_item=get_config_table_row_item,
    )

    template_name = "core/environment_index.html"
    if hx_target(request, lambda x: x.startswith("config_table_row")):
        if action == "edit":
            template_name += "#config_table_row_form"
        else:
            template_name += "#config_table_row_view"

    return TemplateResponse(request, template_name, context)
