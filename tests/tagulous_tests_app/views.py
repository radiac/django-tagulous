"""
Tagulous test app views
"""
from __future__ import unicode_literals

from django.utils import six
from django.views.generic.edit import CreateView, UpdateView

# Django 1.10 deprecates urlresolvers
try:
    from django.urls import reverse_lazy
except ImportError:
    from django.core.urlresolvers import reverse_lazy

from tests.tagulous_tests_app import models


def null(request):
    "Null view for reversing"
    return None

class MixedCreate(CreateView):
    model = models.SimpleMixedTest
    fields = ['name', 'singletag', 'tags']
    success_url = reverse_lazy('tagulous_tests_app-null')

class MixedUpdate(UpdateView):
    model = models.SimpleMixedTest
    fields = ['name', 'singletag', 'tags']
    success_url = reverse_lazy('tagulous_tests_app-null')
