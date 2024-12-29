import re
from django.http import HttpResponse, HttpResponseBadRequest
from django.template import Context, RequestContext, Template
import django_magic_context as magic
from django import forms
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _

from core.contexts.breadcrumbs import get_breadcrumbs
from core.models import ConfigItem, ConfigItemValue, Environment, Service
from core.types import ConfigTable, ConfigTableRow


def cget(context, key):
    value = context[key]
    if callable(value):
        return value()
    return value


def get_action(request) -> str:
    return request.GET.get("action")


def get_item(item_id):
    return ConfigItem.objects.get(id=item_id)


def get_item_value(item_id, env_id):
    return ConfigItemValue.objects.filter(
        item_id=item_id, environment_id=env_id
    ).first()


def get_item_form(request, item_id):
    item = ConfigItem.objects.filter(id=item_id).first()

    Form = forms.modelform_factory(model=ConfigItem, fields=["name"])
    if request.method == "GET":
        form = Form(instance=item)
    else:
        form = Form(request.POST, instance=item)

    return form


def get_item_value_form(request, item_id, env_id):
    if not item_id and env_id:
        return None

    value = ConfigItemValue.objects.filter(
        item_id=item_id, environment_id=env_id
    ).first()

    Form = forms.modelform_factory(model=ConfigItemValue, fields=["value"])
    if request.method == "GET":
        form = Form(instance=value)
    else:
        form = Form(request.POST, instance=value)

    setattr(form, "env_id", env_id)
    setattr(form, "item_id", item_id)
    return form


def get_environments(org, project, service):
    environments = Environment.objects.filter(
        service=service,
        service__project=project,
        service__project__organization=org,
    ).order_by("name")
    return environments


def get_config_table(org, project, service, environments) -> ConfigTable:
    items = ConfigItem.objects.filter(
        service=service,
        service__project=project,
        service__project__organization=org,
    ).order_by("name")

    values_dict = {
        (item_value.item_id, item_value.environment_id): item_value
        for item_value in ConfigItemValue.objects.filter(item_id__in=items)
    }

    rows = [
        ConfigTableRow(
            item=item,
            values=[values_dict.get((item.id, env.id)) for env in environments],
        )
        for item in items
    ]

    return ConfigTable(
        headers=[
            _("Name"),
            *[e.name for e in environments],
        ],
        rows=rows,
    )


def make_context(request, org_id, project_id, service_id):
    service = get_object_or_404(
        Service.objects.select_related(
            "project",
            "project__organization",
        ),
        id=service_id,
        project_id=project_id,
        project__organization_id=org_id,
    )

    return magic.resolve(
        request=request,
        action=get_action,
        user=request.user,
        org_id=org_id,
        project_id=project_id,
        service_id=service_id,
        org=service.project.organization,
        project=service.project,
        service=service,
        environments=get_environments,
        config_table=get_config_table,
        breadcrumbs=get_breadcrumbs,
    )


def render_component(context, name, **kwargs):
    request = context["request"]

    attrs = " ".join(f':{key}="{key}"' for key in kwargs.keys())

    ctx = RequestContext(request, kwargs)
    ctx.update(context)

    rendered = Template(f"{{% c {name} {attrs} %}}{{% endc %}}").render(ctx)
    return HttpResponse(rendered)


def render_item_row(context, item) -> HttpResponse:
    environments = cget(context, "environments")

    values_dict = {
        (item_value.item_id, item_value.environment_id): item_value
        for item_value in ConfigItemValue.objects.filter(item=item)
    }

    row = ConfigTableRow(
        item=item,
        values=[values_dict.get((item.id, env.id)) for env in environments],
    )
    return render_component(context, "config.row", row=row, environments=environments)


def handle_item(context, item_id, action):
    request = cget(context, "request")

    match (request.method, action):
        case ("GET", "view"):
            item = get_item(item_id)
            return render_component(context, "config.item", item=item)

        case ("GET", action) if action in ("new", "edit"):
            form = get_item_form(request, item_id)
            return render_component(context, "config.item-form", form=form)

        case ("POST", action) if action in ("new", "edit"):
            form = get_item_form(request, item_id)
            is_new = not form.instance.id
            if not form.is_valid():
                return render_component(context, "config.item-form", form=form)

            item = form.save(commit=False)
            item.type = ConfigItem.Type.ENV
            item.service = cget(context, "service")
            item.save()

            if is_new:
                return render_item_row(context, form.instance)

            return render_component(context, "config.item", item=item)

        case ("DELETE", "edit"):
            ConfigItem.objects.filter(id=item_id).delete()
            return HttpResponse()

    return HttpResponseBadRequest()


def handle_item_value(context, item_id, env_id, action):
    request = cget(context, "request")

    match (request.method, action):
        case ("GET", "view"):
            value = get_item_value(item_id, env_id)
            return render_component(
                context,
                "config.item-value",
                item_id=item_id,
                env_id=env_id,
                value=value,
            )

        case ("GET", "edit"):
            form = get_item_value_form(request, item_id, env_id)
            return render_component(context, "config.item-value-form", form=form)

        case ("POST", "edit"):
            form = get_item_value_form(request, item_id, env_id)
            if not form.is_valid():
                return render_component(context, "config.item-value-form", form=form)

            value = form.save(commit=False)
            value.item_id = item_id
            value.environment_id = env_id
            value.save()

            return render_component(
                context,
                "config.item-value",
                item_id=item_id,
                env_id=env_id,
                value=value,
            )

        case ("DELETE", "edit"):
            ConfigItemValue.objects.filter(
                item_id=item_id, environment_id=env_id
            ).delete()
            return render_component(
                context,
                "config.item-value",
                item_id=item_id,
                env_id=env_id,
                value=None,
            )

    return HttpResponseBadRequest()


def view(
    request,
    org_id,
    project_id,
    service_id,
    item_id=None,
    action=None,
    resource=None,
    env_id=None,
):
    context = make_context(request, org_id, project_id, service_id)

    if resource == "items":
        if response := handle_item(context, item_id, action):
            return response

    elif resource == "values":
        if response := handle_item_value(context, item_id, env_id, action):
            return response

    return TemplateResponse(request, f"core/service_index.html", context)
