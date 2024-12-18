from types import SimpleNamespace
from django.contrib import admin
from django.urls import path, include

from core import views as core_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", core_views.index, name="index"),
]
