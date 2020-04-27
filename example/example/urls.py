"""example URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from __future__ import unicode_literals

from django.conf.urls import include, url
from django.contrib import admin
from django.utils import six
import tagulous.views

from example import views
from example import models


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(
        r'^api/skills/$',
        tagulous.views.autocomplete,
        {'tag_model': models.Skill},
        name='person_skills_autocomplete',
    ),
    url(r'^$', views.index),
]
