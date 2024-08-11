from django.contrib import admin
from django.urls import path, re_path

import tagulous.views

from . import models, views

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "api/skills/",
        tagulous.views.autocomplete,
        {"tag_model": models.Skill},
        name="person_skills_autocomplete",
    ),
    re_path(r"^(?P<person_pk>\d+)/$", views.index, name="edit"),
    path("", views.index, name="index"),
]
