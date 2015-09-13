"""
Tagulous test app urls

Usage:
    class MyTestCase(TestCase):
        urls = 'tests.tagulous_tests_app.urls'
"""

import django
from django.conf.urls import include, patterns, url
if django.VERSION < (1, 8):
    # Django 1.7 or earlier
    mk_urlpatterns = lambda *urls: patterns('', *urls)
else:
    mk_urlpatterns = lambda *urls: list(urls)

import tagulous.views
from tests.tagulous_tests_app import models, views


tagged_model = models.TagFieldOptionsModel

urlpatterns = mk_urlpatterns(
    url(r'^tagulous_tests_app/', include(mk_urlpatterns(
        # CBV with tagged forms
        url(r'views/$', views.null, name='tagulous_tests_app-null'),
        url(r'views/MixedCreate/$',
            views.MixedCreate.as_view(),
            name='tagulous_tests_app-MixedCreate',
        ),
        url(r'views/MixedUpdate/(?P<pk>[0-9]+)/$',
            views.MixedUpdate.as_view(),
            name='tagulous_tests_app-MixedUpdate',
        ),
        
        # Tagulous autocomplete
        url(r'^autocomplete/unlimited/$',
            tagulous.views.autocomplete,
            {'tag_model': tagged_model.autocomplete_view.tag_model},
            name='tagulous_tests_app-unlimited',
        ),
        url(r'^autocomplete/limited/$',
            tagulous.views.autocomplete,
            {'tag_model': tagged_model.autocomplete_limit.tag_model},
            name='tagulous_tests_app-limited',
        ),
        url(r'^autocomplete/unlimited/login/$',
            tagulous.views.autocomplete_login,
            {'tag_model': tagged_model.autocomplete_view.tag_model},
            name='tagulous_tests_app-login',
        ),
        url(r'^autocomplete/unlimited/queryset/$',
            tagulous.views.autocomplete,
            {'tag_model': tagged_model.autocomplete_view.tag_model.objects.filter(
                name__startswith='tag2',
            )},
            name='tagulous_tests_app-queryset',
        ),
        url(r'^autocomplete/unlimited/force_lowercase_true/$',
            tagulous.views.autocomplete,
            {'tag_model': tagged_model.force_lowercase_true.tag_model},
            name='tagulous_tests_app-force_lowercase_true',
        ),
        url(r'^autocomplete/unlimited/case_sensitive_false/$',
            tagulous.views.autocomplete,
            {'tag_model': tagged_model.case_sensitive_false.tag_model},
            name='tagulous_tests_app-case_sensitive_false',
        ),
        url(r'^autocomplete/unlimited/case_sensitive_true/$',
            tagulous.views.autocomplete,
            {'tag_model': tagged_model.case_sensitive_true.tag_model},
            name='tagulous_tests_app-case_sensitive_true',
        ),
    )))
)

