"""
Tagulous test app urls

Usage:
    class MyTestCase(TestCase):
        urls = 'tagulous.tests.app.urls'
"""

try:
    from django.conf.urls.defaults import include, patterns, url
except ImportError:
    from django.conf.urls import include, patterns, url

from tagulous.tests.app import models, views


urlpatterns = patterns('',
    url(r'^tagulous_tests_app/', include(patterns('',
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
            'tagulous.views.autocomplete',
            {'tag_model': models.TagFieldOptionsModel.autocomplete_view.tag_model},
            name='tagulous_tests_app-unlimited',
        ),
        url(r'^autocomplete/limited/$',
            'tagulous.views.autocomplete',
            {'tag_model': models.TagFieldOptionsModel.autocomplete_limit.tag_model},
            name='tagulous_tests_app-limited',
        ),
    )))
)
