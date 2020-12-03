"""
Tagulous test app urls

Usage:
    class MyTestCase(TestCase):
        urls = 'tests.tagulous_tests_app.urls'
"""
from django.conf.urls import include, re_path

import tagulous.views
from tests.tagulous_tests_app import models, views


tagged_model = models.TagFieldOptionsModel

urlpatterns = [
    # We don't include the admin site here - that's added by AdminTestManager
    re_path(
        r"^tagulous_tests_app/",
        include(
            [
                # CBV with tagged forms
                re_path(r"views/$", views.null, name="tagulous_tests_app-null"),
                re_path(
                    r"views/MixedCreate/$",
                    views.MixedCreate.as_view(),
                    name="tagulous_tests_app-MixedCreate",
                ),
                re_path(
                    r"views/MixedUpdate/(?P<pk>[0-9]+)/$",
                    views.MixedUpdate.as_view(),
                    name="tagulous_tests_app-MixedUpdate",
                ),
                # Tagulous autocomplete
                re_path(
                    r"^autocomplete/unlimited/$",
                    tagulous.views.autocomplete,
                    {"tag_model": tagged_model.autocomplete_view.tag_model},
                    name="tagulous_tests_app-unlimited",
                ),
                re_path(
                    r"^autocomplete/limited/$",
                    tagulous.views.autocomplete,
                    {"tag_model": tagged_model.autocomplete_limit.tag_model},
                    name="tagulous_tests_app-limited",
                ),
                re_path(
                    r"^autocomplete/unlimited/login/$",
                    tagulous.views.autocomplete_login,
                    {"tag_model": tagged_model.autocomplete_view.tag_model},
                    name="tagulous_tests_app-login",
                ),
                re_path(
                    r"^autocomplete/unlimited/queryset/$",
                    tagulous.views.autocomplete,
                    {
                        "tag_model": tagged_model.autocomplete_view.tag_model.objects.filter(
                            name__startswith="tag2"
                        )
                    },
                    name="tagulous_tests_app-queryset",
                ),
                re_path(
                    r"^autocomplete/unlimited/force_lowercase_true/$",
                    tagulous.views.autocomplete,
                    {"tag_model": tagged_model.force_lowercase_true.tag_model},
                    name="tagulous_tests_app-force_lowercase_true",
                ),
                re_path(
                    r"^autocomplete/unlimited/case_sensitive_false/$",
                    tagulous.views.autocomplete,
                    {"tag_model": tagged_model.case_sensitive_false.tag_model},
                    name="tagulous_tests_app-case_sensitive_false",
                ),
                re_path(
                    r"^autocomplete/unlimited/case_sensitive_true/$",
                    tagulous.views.autocomplete,
                    {"tag_model": tagged_model.case_sensitive_true.tag_model},
                    name="tagulous_tests_app-case_sensitive_true",
                ),
            ]
        ),
    ),
]
