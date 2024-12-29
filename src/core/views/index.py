import django_magic_context as magic
from django.template.response import TemplateResponse


def view(request):
    context = magic.resolve()

    return TemplateResponse(request, "core/index.html", context)
