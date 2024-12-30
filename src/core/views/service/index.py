from collections import defaultdict
from typing import Any, Callable
from attrs import define, field
from django.http import HttpResponse
from django.template import RequestContext, Template
from django.urls import path
import django_magic_context as magic
from django import forms
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _

from core.contexts.breadcrumbs import get_breadcrumbs
from core.models import ConfigItem, ConfigItemValue, Environment, Service
from core.types import ConfigTable, ConfigTableRow


@define
class Dispatcher:
    context_factory: Callable[..., dict[str, Any]]

    registry: Any = field(factory=lambda: defaultdict(list))
    paths: list[Any] = field(factory=list)

    @property
    def urls(self):
        return self.paths

    def guard(self, *paths, **kwargs):
        def decorator(decoratee):
            for p in paths:
                self.registry[p.name].append((kwargs, decoratee))
                self.paths.append(p)

            return decoratee

        return decorator

    def path(self, *args, **kwargs):
        return path(*args, view=self.view, **kwargs)

    def view(self, request, **kwargs):
        context = self.context_factory(request, **kwargs)

        for expectations, handler in self.registry[request.resolver_match.url_name]:
            for key, expected_value in expectations.items():
                try:
                    value = cget(context, key)
                except KeyError:
                    break

                if callable(expected_value):
                    if not expected_value(value):
                        break
                else:
                    if value != expected_value:
                        break
            else:
                return handler(context)


NO_DEFAULT = object()


def cget(context, *keys, default=NO_DEFAULT):
    result = []
    for key in keys:
        if default is NO_DEFAULT:
            value = context[key]
        else:
            value = context.get(key, default)
        if callable(value):
            result.append(value())
        else:
            result.append(value)

    if len(result) == 1:
        return result[0]

    return result


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


def make_context(request, org_id, project_id, service_id, **kwargs):
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
        method=request.method,
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
        **kwargs,
    )


def render_component(context, name, **kwargs):
    request = context["request"]

    attrs = " ".join(f':{key}="{key}"' for key in kwargs.keys())

    request_context = RequestContext(request, kwargs)
    request_context.update(context)

    template = Template(f"{{% c {name} {attrs} %}}{{% endc %}}")
    rendered = template.render(request_context)
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


def render_item(context, item) -> HttpResponse:
    return render_component(context, "config.item", item=item)


def render_item_form(context, form) -> HttpResponse:
    return render_component(context, "config.item-form", form=form)


view = Dispatcher(make_context)


@view.guard(
    view.path("items/<int:item_id>/", name="service-item"),
    method="GET",
)
def handle_item_get(context):
    item_id = cget(context, "item_id")
    item = get_item(item_id)
    return render_item(context, item)


@view.guard(
    view.path("items/", name="service-item-list"),
    view.path("items/<int:item_id>/", name="service-item"),
    method="POST",
)
def handle_item_post(context):
    request = cget(context, "request")
    item_id = cget(context, "item_id", default=None)
    form = get_item_form(request, item_id)
    is_new = not form.instance.id
    if not form.is_valid():
        return render_item_form(context, form)

    item = form.save(commit=False)
    item.type = ConfigItem.Type.ENV
    item.service = cget(context, "service")
    item.save()

    if is_new:
        return render_item_row(context, form.instance)

    return render_item(context, item)


@view.guard(
    view.path("items/<int:item_id>/", name="service-item"),
    method="DELETE",
)
def handle_item_delete(context):
    item_id = cget(context, "item_id")
    ConfigItem.objects.filter(id=item_id).delete()
    return HttpResponse()


@view.guard(
    view.path("items/new/", name="service-item-new"),
    view.path("items/<int:item_id>/edit/", name="service-item-form"),
    method="GET",
)
def handle_item_edit(context):
    request = cget(context, "request")
    item_id = cget(context, "item_id", default=None)
    form = get_item_form(request, item_id)
    return render_item_form(context, form)


@view.guard(
    view.path("items/<int:item_id>/env/<int:env_id>/", name="service-value"),
    method="GET",
)
def handle_value_get(context):
    item_id, env_id = cget(context, "item_id", "env_id")
    value = get_item_value(item_id, env_id)
    return render_component(
        context, "config.item-value", item_id=item_id, env_id=env_id, value=value
    )


@view.guard(
    view.path("items/<int:item_id>/env/<int:env_id>/", name="service-value"),
    method="POST",
)
def handle_value_post(context):
    request, item_id, env_id = cget(context, "request", "item_id", "env_id")
    form = get_item_value_form(request, item_id, env_id)
    if not form.is_valid():
        return render_component(context, "config.item-value-form", form=form)

    value = form.save(commit=False)
    value.item_id = item_id
    value.environment_id = env_id
    value.save()

    return render_component(
        context, "config.item-value", item_id=item_id, env_id=env_id, value=value
    )


@view.guard(
    view.path("items/<int:item_id>/env/<int:env_id>/", name="service-value"),
    method="DELETE",
)
def handle_value_delete(context):
    item_id, env_id = cget(context, "item_id", "env_id")
    ConfigItemValue.objects.filter(item_id=item_id, environment_id=env_id).delete()
    return render_component(
        context, "config.item-value", item_id=item_id, env_id=env_id, value=None
    )


@view.guard(
    view.path("items/<int:item_id>/env/<int:env_id>/edit/", name="service-value-form"),
    method="GET",
)
def handle_value_edit(context):
    request, item_id, env_id = cget(context, "request", "item_id", "env_id")
    form = get_item_value_form(request, item_id, env_id)
    return render_component(context, "config.item-value-form", form=form)


@view.guard(
    view.path("", name="service-detail"),
    method="GET",
)
def handle_get(context):
    request = cget(context, "request")
    return TemplateResponse(request, "core/service_index.html", context)
