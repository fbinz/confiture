from typing import Any, Callable
from django.http.response import HttpResponse
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from django import forms
import django_magic_context as magic
from attrs import define


class ConfigTableRowForm(forms.Form):
    name = forms.CharField()
    value = forms.CharField()

    def __init__(self, *args, id, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = id


db = {
    "1": dict(
        id="1",
        name="DJANGO_DEBUG",
        value="True",
    ),
    "2": dict(
        id="2",
        name="DJANGO_DATABASE_URL",
        value="postgresql://123:456@localhost/db",
    ),
}


@define
class ConfigTable:
    headers: list[str]
    rows: list[Any]


def get_config_table() -> ConfigTable:
    return ConfigTable(headers=[_("Name"), _("Value")], rows=db.values())


def get_config_table_row_form(item_id):
    item = db.get(item_id)
    return ConfigTableRowForm(id=item_id, data=item)


def get_config_table_row_item(item_id):
    item = db.get(item_id)
    return item


def hx_target(request, test: Callable[[str], bool]) -> bool:
    header = request.headers.get(f"HX-Target")
    if not header:
        return False

    return test(header)


def handle_save(request, item_id):
    form = ConfigTableRowForm(request.POST, id=item_id)
    if form.is_valid():
        item = db.get(item_id)
        if item:
            item["name"] = form.cleaned_data["name"]
            item["value"] = form.cleaned_data["value"]


def handle_delete(request, item_id):
    del db[item_id]
    return HttpResponse(status=200)


def index(request):
    item_id = request.GET.get("item")

    context = magic.resolve(
        request=request,
        item_id=item_id,
        config_table=get_config_table,
        config_table_row_form=get_config_table_row_form,
        config_table_row_item=get_config_table_row_item,
    )

    action = request.GET.get("action")
    method = request.method

    if action == "save" and method == "POST" and item_id:
        handle_save(request, item_id)
    elif action == "delete" and item_id:
        return handle_delete(request, item_id)

    template_name = "core/index.html"
    if hx_target(request, lambda x: x.startswith("config_table_row")):
        if action == "edit":
            template_name += "#config_table_row_form"
        else:
            template_name += "#config_table_row_view"

    return TemplateResponse(request, template_name, context)
