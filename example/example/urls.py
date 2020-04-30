from __future__ import unicode_literals

from django.conf.urls import url
from django.contrib import admin

import tagulous.views
from example import models, views


urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url(
        r"^api/skills/$",
        tagulous.views.autocomplete,
        {"tag_model": models.Skill},
        name="person_skills_autocomplete",
    ),
    url(r"^$", views.index),
]
