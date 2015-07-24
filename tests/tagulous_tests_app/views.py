"""
Tagulous test app views
"""
from django.core.urlresolvers import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView

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
